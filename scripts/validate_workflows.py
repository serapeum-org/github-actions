"""Static contract test for the repository's GitHub Actions workflows.

This repository ships no application code, so its "unit tests" are the workflow
definitions themselves. This script is the test that guards *those*: it parses
every file under ``.github/workflows`` and asserts the invariants that the CI
fan-out (``ci.yml``) depends on. A violation of any invariant is a real defect
that would otherwise only surface as a broken or double-running pipeline after a
merge to ``main``.

Invariants checked:

* **Valid and named** — every workflow parses as YAML and declares ``name`` and
  ``on``.
* **Reusable-workflow wiring** — every local workflow invoked by ``ci.yml`` via
  ``uses: ./.github/workflows/<file>`` exists and declares a ``workflow_call``
  trigger, so the orchestrator can actually call it.
* **No double-run on main** — every workflow that both has a ``push`` trigger and
  is called by ``ci.yml`` excludes ``main`` from that trigger
  (``branches-ignore: [main]``). Main is driven only through the orchestrator.
* **Least privilege** — ``ci.yml`` runs with ``contents: read`` at the workflow
  level; the only elevated grant is the ``deploy-docs`` job's ``contents:
  write``.
* **Scoped secrets** — ``ci.yml`` never uses ``secrets: inherit``; the single
  user-defined secret (``PYPI_TEST_PUBLISH``) is passed only to the
  ``release-pypi`` job.
* **Serialized deploy** — ``deploy-docs`` declares a ``concurrency`` group so two
  near-simultaneous merges cannot race on the ``gh-pages`` push.

Run it directly::

    python scripts/validate_workflows.py

It prints every violation it finds and exits non-zero if there is at least one,
so it can be wired straight into CI.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

#: Directory holding the workflow definitions, relative to the repository root.
WORKFLOWS_DIR = Path(".github/workflows")

#: The orchestrator workflow that fans out to the rest on a push to ``main``.
ORCHESTRATOR = "ci.yml"

#: The only user-defined secret in the repository.
PYPI_SECRET = "PYPI_TEST_PUBLISH"


def get_on(workflow: dict[str, Any]) -> dict[str, Any]:
    """Return a workflow's trigger mapping, normalizing the YAML ``on`` quirk.

    PyYAML parses the bare key ``on:`` as the boolean ``True`` (YAML 1.1 treats
    ``on``/``off`` as booleans), so the trigger block can land under either the
    string ``"on"`` or the boolean ``True`` depending on quoting.

    Args:
        workflow: A parsed workflow document.

    Returns:
        The trigger mapping, or an empty dict if the workflow declares no
        triggers or declares them in list/shorthand form.
    """
    on = workflow.get("on", workflow.get(True))
    return on if isinstance(on, dict) else {}


def load_workflows() -> dict[str, dict[str, Any]]:
    """Parse every ``*.yml`` workflow in :data:`WORKFLOWS_DIR`.

    Returns:
        A mapping of file name (e.g. ``"ci.yml"``) to the parsed document.
        Files that fail to parse are omitted; callers detect that via the
        separately reported parse errors.
    """
    workflows: dict[str, dict[str, Any]] = {}
    for path in sorted(WORKFLOWS_DIR.glob("*.yml")):
        workflows[path.name] = yaml.safe_load(path.read_text(encoding="utf-8"))
    return workflows


def called_workflows(orchestrator: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return the ``ci.yml`` jobs that call a local reusable workflow.

    Args:
        orchestrator: The parsed ``ci.yml`` document.

    Returns:
        A mapping of called workflow file name to the calling job's body, for
        every job whose ``uses`` points at ``./.github/workflows/<file>``.
    """
    calls: dict[str, dict[str, Any]] = {}
    for job in orchestrator.get("jobs", {}).values():
        uses = job.get("uses", "")
        prefix = "./.github/workflows/"
        if isinstance(uses, str) and uses.startswith(prefix):
            calls[uses[len(prefix):]] = job
    return calls


def check_named(workflows: dict[str, dict[str, Any]]) -> list[str]:
    """Check that every workflow declares ``name`` and some trigger."""
    problems: list[str] = []
    for fname, wf in workflows.items():
        if not isinstance(wf, dict):
            problems.append(f"{fname}: not a mapping / failed to parse")
            continue
        if "name" not in wf:
            problems.append(f"{fname}: missing top-level 'name'")
        if not get_on(wf):
            problems.append(f"{fname}: missing or non-mapping 'on' triggers")
    return problems


def check_wiring(workflows: dict[str, dict[str, Any]], calls: dict[str, dict[str, Any]]) -> list[str]:
    """Check that every workflow called by ``ci.yml`` exists and is callable."""
    problems: list[str] = []
    for target in calls:
        if target not in workflows:
            problems.append(f"{ORCHESTRATOR} calls '{target}', which does not exist")
            continue
        if "workflow_call" not in get_on(workflows[target]):
            problems.append(f"{target}: called by {ORCHESTRATOR} but has no 'workflow_call' trigger")
    return problems


def check_no_double_run(workflows: dict[str, dict[str, Any]], calls: dict[str, dict[str, Any]]) -> list[str]:
    """Check the no-double-run guard: called workflows exclude ``main`` from push."""
    problems: list[str] = []
    for target in calls:
        wf = workflows.get(target)
        if not wf:
            continue
        push = get_on(wf).get("push")
        if not isinstance(push, dict):
            continue  # No path-filtered push trigger (e.g. deploy-docs) → cannot double-run.
        ignored = push.get("branches-ignore") or []
        if "main" not in ignored:
            problems.append(
                f"{target}: has a 'push' trigger and is called by {ORCHESTRATOR}, "
                f"but does not set branches-ignore: [main] (would double-run on merge)"
            )
    return problems


def check_least_privilege(orchestrator: dict[str, Any]) -> list[str]:
    """Check ``ci.yml`` is read-only except for the deploy-docs job's write grant."""
    problems: list[str] = []
    top = orchestrator.get("permissions")
    if top != {"contents": "read"}:
        problems.append(f"{ORCHESTRATOR}: top-level permissions should be {{contents: read}}, got {top!r}")
    for name, job in orchestrator.get("jobs", {}).items():
        perms = job.get("permissions")
        if perms and perms != {"contents": "read"} and name != "deploy-docs":
            problems.append(f"{ORCHESTRATOR}: job '{name}' grants unexpected permissions {perms!r}")
    return problems


def check_secrets(orchestrator: dict[str, Any], calls: dict[str, dict[str, Any]]) -> list[str]:
    """Check secrets are scoped: no blanket inherit, PyPI token only to release-pypi."""
    problems: list[str] = []
    for name, job in calls.items():
        secrets = job.get("secrets")
        if secrets == "inherit":
            problems.append(f"{ORCHESTRATOR}: job calling '{name}' uses blanket 'secrets: inherit'")
        if isinstance(secrets, dict) and PYPI_SECRET in secrets and name != "test-release-pypi.yml":
            problems.append(f"{ORCHESTRATOR}: '{PYPI_SECRET}' passed to '{name}', which does not need it")
    return problems


def check_deploy_concurrency(workflows: dict[str, dict[str, Any]]) -> list[str]:
    """Check ``deploy-docs`` declares a concurrency group to serialize gh-pages pushes."""
    deploy = workflows.get("deploy-docs.yml")
    if deploy and not deploy.get("concurrency"):
        return ["deploy-docs.yml: missing a 'concurrency' group (gh-pages push could race)"]
    return []


def main() -> int:
    """Run every check and report the outcome.

    Returns:
        ``0`` if all invariants hold, ``1`` otherwise.
    """
    problems: list[str] = []

    for path in sorted(WORKFLOWS_DIR.glob("*.yml")):
        try:
            yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as err:
            problems.append(f"{path.name}: YAML parse error: {err}")

    workflows = load_workflows()
    orchestrator = workflows.get(ORCHESTRATOR)
    if orchestrator is None:
        print(f"FAIL: orchestrator '{ORCHESTRATOR}' not found", file=sys.stderr)
        return 1

    calls = called_workflows(orchestrator)

    problems += check_named(workflows)
    problems += check_wiring(workflows, calls)
    problems += check_no_double_run(workflows, calls)
    problems += check_least_privilege(orchestrator)
    problems += check_secrets(orchestrator, calls)
    problems += check_deploy_concurrency(workflows)

    if problems:
        print(f"Workflow contract violations ({len(problems)}):")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print(f"OK: {len(workflows)} workflows satisfy the contract "
          f"({len(calls)} reusable workflows wired into {ORCHESTRATOR}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
