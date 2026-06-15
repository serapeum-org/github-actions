"""Populate notebook outputs before ``mkdocs build`` (CI-side helper).

Vendored inside the ``mkdocs-deploy`` composite action and invoked via
``${{ github.action_path }}/scripts/prep_notebooks.py`` when the caller sets
``notebooks-path``. Walks the notebook tree and uses ``.jupyter_cache/`` as a
content-addressed store:

* If a cached executed copy already exists for a given notebook, it is copied
  back over the working-tree notebook.
* Otherwise the notebook is executed in place (via ``jupyter nbconvert
  --execute --inplace``) and then saved into the cache for next time.

The ``.jupyter_cache/`` directory is itself persisted across CI runs by
``actions/cache`` keyed on the notebooks, ``src/**/*.py``, and
``pyproject.toml`` hash.

Env vars:
    NOTEBOOK_ROOT  Root directory to walk for ``*.ipynb`` files (required).
    NOTEBOOK_EXCLUDE  Newline- or comma-separated glob patterns (matched
        case-sensitively against each notebook's path relative to
        NOTEBOOK_ROOT) to skip executing. Optional; default skips nothing.
    NOTEBOOK_CONTINUE_ON_ERROR  When ``"true"``, a non-excluded notebook that
        fails to execute is logged as a warning and the walk continues instead
        of aborting. Optional; default ``"false"``.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from fnmatch import fnmatchcase
from pathlib import Path

NOTEBOOK_ROOT = Path(os.environ["NOTEBOOK_ROOT"])
CACHE_ROOT = Path(".jupyter_cache/executed")
TIMEOUT = "600"

EXCLUDE = [
    pat.strip()
    for chunk in os.environ.get("NOTEBOOK_EXCLUDE", "").splitlines()
    for pat in chunk.split(",")
    if pat.strip()
]
CONTINUE_ON_ERROR = os.environ.get("NOTEBOOK_CONTINUE_ON_ERROR", "").strip().lower() == "true"


def _matches(rel_posix: str, pat: str) -> bool:
    """Match a POSIX relative path against one glob pattern (case-sensitively).

    Matching uses ``fnmatchcase``. As a special case, a leading ``**/`` also
    matches zero directories: the pattern is retried with the ``**/`` prefix
    stripped so ``**/stac-cloud-*.ipynb`` matches a top-level
    ``stac-cloud-foo.ipynb`` as well as nested ones.
    """
    if fnmatchcase(rel_posix, pat):
        return True
    if pat.startswith("**/") and fnmatchcase(rel_posix, pat[3:]):
        return True
    return False


def is_excluded(nb_path: Path) -> bool:
    """Return True if a notebook's relative path matches any exclude pattern."""
    rel_posix = nb_path.relative_to(NOTEBOOK_ROOT).as_posix()
    return any(_matches(rel_posix, pat) for pat in EXCLUDE)


def cached_path_for(nb_path: Path) -> Path:
    """Return the cache location that mirrors a notebook's path."""
    rel = nb_path.relative_to(NOTEBOOK_ROOT)
    return CACHE_ROOT / rel


def execute_in_place(nb_path: Path) -> None:
    """Execute a notebook in place using ``jupyter nbconvert``."""
    subprocess.run(
        [
            sys.executable,
            "-m",
            "jupyter",
            "nbconvert",
            "--to",
            "notebook",
            "--execute",
            "--inplace",
            f"--ExecutePreprocessor.timeout={TIMEOUT}",
            str(nb_path),
        ],
        check=True,
    )


def main() -> int:
    if not NOTEBOOK_ROOT.exists():
        print(f"Notebook root {NOTEBOOK_ROOT} does not exist.", file=sys.stderr)
        return 1

    CACHE_ROOT.mkdir(parents=True, exist_ok=True)

    candidates = [
        nb
        for nb in sorted(NOTEBOOK_ROOT.rglob("*.ipynb"))
        if ".ipynb_checkpoints" not in nb.parts
    ]

    notebooks, skipped = [], 0
    for nb in candidates:
        if is_excluded(nb):
            print(f"[excluded]   {nb}")
            skipped += 1
        else:
            notebooks.append(nb)

    hits, misses, failures = 0, 0, 0
    for nb in notebooks:
        cached = cached_path_for(nb)
        if cached.exists():
            print(f"[cache hit]  {nb}")
            shutil.copy2(cached, nb)
            hits += 1
        else:
            print(f"[cache miss] executing {nb}")
            try:
                execute_in_place(nb)
            except subprocess.CalledProcessError as exc:
                if not CONTINUE_ON_ERROR:
                    raise
                print(f"::warning::Notebook execution failed, continuing: {nb} ({exc})")
                failures += 1
                continue
            cached.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(nb, cached)
            misses += 1

    print(
        f"Done: {hits} hits, {misses} misses, {failures} failures, "
        f"{skipped} excluded, {len(notebooks)} executed-or-cached."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
