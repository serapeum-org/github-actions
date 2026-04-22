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
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

NOTEBOOK_ROOT = Path(os.environ["NOTEBOOK_ROOT"])
CACHE_ROOT = Path(".jupyter_cache/executed")
TIMEOUT = "600"


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

    notebooks = [
        nb
        for nb in sorted(NOTEBOOK_ROOT.rglob("*.ipynb"))
        if ".ipynb_checkpoints" not in nb.parts
    ]

    hits, misses = 0, 0
    for nb in notebooks:
        cached = cached_path_for(nb)
        if cached.exists():
            print(f"[cache hit]  {nb}")
            shutil.copy2(cached, nb)
            hits += 1
        else:
            print(f"[cache miss] executing {nb}")
            execute_in_place(nb)
            cached.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(nb, cached)
            misses += 1

    print(f"Done: {hits} hits, {misses} misses, {len(notebooks)} notebooks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
