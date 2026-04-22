# Integrating notebook execution + caching into `mkdocs-deploy`

## Context

The `statista` repo currently runs notebook execution and caching **outside** the
`mkdocs-deploy` composite action, in its own workflow
(`.github/workflows/github-pages-mkdocs.yml`). Every deploy job (PR, main,
release) repeats the same 3-step prelude before calling `mkdocs-deploy`:

1. `actions/setup-python@v5` (separate from the mkdocs env)
2. `actions/cache@v4` to restore `.jupyter_cache/`
3. `pip install -e . jupyter nbconvert ipykernel` + `python scripts/prep_notebooks.py`

Goal: fold this prelude into `actions/mkdocs-deploy/action.yml` so any repo with
executable notebooks can enable it with one input, and the boilerplate at the
call site disappears.

## What the statista workflow does today

For each of the three jobs (`deploy-pr`, `deploy-main`, `deploy-release`):

| Step                                                                                | Purpose                                                                                     |
|-------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| `actions/checkout@v5` with `fetch-depth: 0`                                         | Full history (release job also pins `ref` to `workflow_run.head_branch`)                    |
| `actions/setup-python@v5`                                                           | Light Python for the prep step (separate from the mkdocs env the composite action installs) |
| `actions/cache@v4` on `.jupyter_cache`                                              | Restore content-addressed store of executed notebooks                                       |
| `pip install -e . jupyter nbconvert ipykernel` + `python scripts/prep_notebooks.py` | Populate working-tree notebooks with outputs                                                |
| `mkdocs-deploy@mkdocs/v1`                                                           | Build + push; mkdocs-jupyter runs with `execute: false` and reads the populated outputs     |

Cache key:
```
jupyter-cache-${{ hashFiles('docs/notebook/**/*.ipynb', 'src/statista/**/*.py', 'pyproject.toml') }}
```
with a `jupyter-cache-` restore-key fallback. Cache save is implicit from
`actions/cache@v4`'s post-action when the key was new.

### `scripts/prep_notebooks.py` summary

- Walks `docs/notebook/**/*.ipynb` (skips `.ipynb_checkpoints`).
- For each notebook:
  - **cache hit** (`.jupyter_cache/executed/<same relative path>` exists) → copy it over the working-tree notebook.
  - **cache miss** → `jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=600 <nb>` and save a copy into the cache.
- Prints hit/miss counts.

## Design decisions

### 1. One Python environment

Use the mkdocs env the action already installs (uv / pip / pixi) to also run
`jupyter nbconvert`. Simpler action code, no redundant Python install.

**Consumer requirement:** `jupyter`, `nbconvert`, and `ipykernel` must be in
whatever dependency group the caller passes via `install-groups` (alongside
the existing `mkdocs-jupyter` requirement).

### 2. Jupyter deps are required in `pyproject.toml`, not auto-installed

The action does NOT install `jupyter`, `nbconvert`, or `ipykernel` itself —
they must be declared in the dependency group the caller passes via
`install-groups`.

Reasons:

- **Reproducibility is the whole point of the cache.** The cache key hashes
  `pyproject.toml`. If jupyter deps aren't there, a kernel upgrade never
  invalidates the cache → stale outputs rendered against an old kernel even
  after the project's kernel version changes.
- **Local / CI parity.** Developers execute notebooks locally. Auto-installing
  jupyter in CI only makes CI's kernel version diverge silently from what
  developers have in their venv.
- **Lockfile integrity.** This repo's CLAUDE.md mandates lock-file
  verification by default. Auto-install would either bypass the lockfile or
  mutate it mid-CI; either regresses on a deliberate principle and would
  force `verify-lock: false` in the inner python-setup call.
- **Silent version conflicts.** If a project pins `ipykernel==6.20`, an
  action-managed `ipykernel>=7` install causes either a silent upgrade or an
  opaque resolver error deep inside the action.

**Fail-fast preflight.** To make the requirement discoverable, add a
preflight import check *before* the prep step runs:

```bash
if ! $PACKAGE_MANAGER run python -c "import jupyter, nbconvert, ipykernel" 2>/dev/null; then
  echo "::error::notebooks-path is set but jupyter/nbconvert/ipykernel are not importable."
  echo "::error::Add them to the dependency group passed via install-groups (currently: '${INSTALL_GROUPS}')."
  exit 1
fi
```

(For `package-manager: pip`, drop the `$PACKAGE_MANAGER run` prefix.)

Consumers who forget get an actionable error on their first CI run, not an
opaque nbconvert stacktrace.

### 3. Cache key is built inside the action

The action builds the cache key itself using conventional paths. The caller
does **not** pass a cache key. No `hashFiles()` expression in the consumer's
workflow.

```yaml
key: jupyter-cache-${{ hashFiles(format('{0}/**/*.ipynb', inputs.notebooks-path), 'src/**/*.py', 'pyproject.toml') }}
```

Three things invalidate the cache:

- Any `.ipynb` file under `notebooks-path` (caller-provided via input).
- Any `.py` file under `src/` (hardcoded; assumes src-layout — the universal
  convention across serapeum-org repos).
- `pyproject.toml` at repo root (hardcoded).

**Uncertainty to verify:** `hashFiles(format(...), 'literal', 'literal')`
inside a composite action step — `hashFiles()` arguments can be expression
results and `format()` is a valid expression function, so they should
compose, but worth smoke-testing with the fixture. Fallback if it doesn't
work: compute the hash in a prior shell step using `git ls-files ... |
xargs sha256sum | sha256sum` and export as a step output.

### 3a. No `restore-keys` fallback

Primary cache key only — any hash change triggers a full re-execute.

The statista workflow today uses `restore-keys: jupyter-cache-` as a prefix
fallback. That fallback interacts badly with `prep_notebooks.py`'s cache-hit
logic: when the primary key misses, the fallback restores cached executed
notebooks from a prior commit, and the script then copies those stale cached
notebooks over the working-tree notebooks — potentially overwriting prose
edits or publishing outputs executed against old library code.

The cache-key hash is supposed to be the guard against staleness;
`restore-keys` deliberately bypasses it. For an opt-in feature where
determinism matters, correctness-by-construction beats partial-cache reuse.
Consumers who need finer-grained cache reuse (per-cell input hashing) should
reach for `jupyter-cache` directly rather than layering fragile fallbacks on
top.

### 4. `prep_notebooks.py` is vendored inside the action

Location: `actions/mkdocs-deploy/scripts/prep_notebooks.py`. The action
invokes it via `${{ github.action_path }}/scripts/prep_notebooks.py`;
consumers never copy or maintain the script themselves.

**Why vendor:**

- **Single source of truth.** The prep logic (cache-hit copy, cache-miss
  execute-and-save, skip `.ipynb_checkpoints`) is tightly coupled to the
  cache layout the action defines. Keeping both in the same repo means the
  script can't drift out of sync with the action.
- **Consumers enable the feature with one flag.** Setting `notebooks-path`
  is the entire integration — no script to copy in.
- **Single place to fix bugs.** Any improvement ships to every consumer on
  the next `@mkdocs-deploy/v1` pull; no per-repo patches.
- **Versioning works naturally.** The script is pinned alongside the action
  via the same tag.

**How the script stays generic:** one env var, `NOTEBOOK_ROOT`, set from the
`notebooks-path` input. Cache location (`.jupyter_cache/executed`) and cell
timeout (`600`) are hardcoded in the script.

```python
NOTEBOOK_ROOT = Path(os.environ["NOTEBOOK_ROOT"])
CACHE_ROOT = Path(".jupyter_cache/executed")
TIMEOUT = "600"
# ... walk NOTEBOOK_ROOT, skip .ipynb_checkpoints,
#     cache-hit → copy cached over working tree,
#     cache-miss → jupyter nbconvert --execute --inplace with TIMEOUT, then save to CACHE_ROOT.
```

### 5. Single input: `notebooks-path`

Setting `notebooks-path` enables the feature; omitting it skips notebook
execution entirely. No separate `execute-notebooks` flag.

- One source of truth — can't misconfigure by setting one without the other.
- No arbitrary default path — defaulting `notebooks-path` to `'docs/notebook'`
  would be a guess; any consumer using `examples/` would have had to
  override it anyway.

## Proposed implementation

### New inputs on `actions/mkdocs-deploy/action.yml`

```yaml
notebooks-path:
  description: >
    Root directory containing notebooks to execute and cache before the
    mkdocs build. When set, the action walks this directory recursively for
    `*.ipynb` files, reuses cached executed copies where available, and runs
    `jupyter nbconvert --execute` for any uncached notebook. Cache is keyed
    on notebook contents, `src/**/*.py`, and `pyproject.toml`, persisted via
    actions/cache. Requires `jupyter`, `nbconvert`, and `ipykernel` in the
    dependency group passed via `install-groups`.
    When empty (default), notebook execution is skipped entirely.
    Examples: 'docs/notebook', 'docs/notebooks', 'examples/notebooks'.
    Default is '' (skip).
  required: false
  default: ''
```

That's the only new input. `src/**/*.py`, `pyproject.toml`, `.jupyter_cache`,
and `600s` cell timeout are all hardcoded inside the action and script.

Additive change → **minor version bump** (`mkdocs-deploy/v1.1.0`), then move
`mkdocs-deploy/v1`. No breaking change for existing consumers.

### New steps, inserted between `python-setup` and `Configure Git`

```yaml
- name: Restore notebook execution cache
  if: ${{ inputs.notebooks-path != '' }}
  uses: actions/cache@v4
  with:
    path: .jupyter_cache
    key: jupyter-cache-${{ hashFiles(format('{0}/**/*.ipynb', inputs.notebooks-path), 'src/**/*.py', 'pyproject.toml') }}
    # No restore-keys on purpose — see §3a. Any hash change = full re-execute.

- name: Verify notebook execution dependencies
  if: ${{ inputs.notebooks-path != '' }}
  shell: bash
  env:
    PACKAGE_MANAGER: ${{ inputs.package-manager }}
    INSTALL_GROUPS: ${{ inputs.install-groups }}
  run: |
    echo "::group::Verifying jupyter / nbconvert / ipykernel are installed"
    if [ "$PACKAGE_MANAGER" = "pip" ]; then
      RUN=""
    else
      RUN="$PACKAGE_MANAGER run"
    fi
    if ! $RUN python -c "import jupyter, nbconvert, ipykernel" 2>/dev/null; then
      echo "::error::notebooks-path is set but jupyter/nbconvert/ipykernel are not importable."
      echo "::error::Add them to the dependency group passed via install-groups (currently: '${INSTALL_GROUPS}')."
      exit 1
    fi
    echo "::endgroup::"

- name: Prepare notebook outputs (execute uncached, merge cached)
  if: ${{ inputs.notebooks-path != '' }}
  shell: bash
  env:
    PACKAGE_MANAGER: ${{ inputs.package-manager }}
    NOTEBOOK_ROOT: ${{ inputs.notebooks-path }}
  run: |
    echo "::group::Preparing notebook outputs"
    SCRIPT="${{ github.action_path }}/scripts/prep_notebooks.py"
    if [ "$PACKAGE_MANAGER" = "pip" ]; then
      python "$SCRIPT"
    else
      $PACKAGE_MANAGER run python "$SCRIPT"
    fi
    echo "::endgroup::"
```

Uses `github.action_path` to locate the vendored script, runs it via
whichever package manager the action already set up so it shares the mkdocs
env.

### Vendored `actions/mkdocs-deploy/scripts/prep_notebooks.py`

Port the statista script with two changes:

- Read `NOTEBOOK_ROOT` from `os.environ` (no default — the step guard
  guarantees it's set).
- Hardcode `CACHE_ROOT = Path(".jupyter_cache/executed")` and
  `TIMEOUT = "600"`.
- Everything else (cache-hit copy, cache-miss execute-then-save,
  `.ipynb_checkpoints` skip, hit/miss logging) carries over unchanged.

### Consumer-side contract to document

Add to `docs/` (and the action README once it exists):

- **Required deps**: `jupyter`, `nbconvert`, `ipykernel`, `mkdocs-jupyter`
  must be in the dependency group the caller passes via `install-groups`.
- **Required mkdocs config**: `mkdocs-jupyter` must be configured with
  `execute: false` so it reads pre-executed outputs instead of re-running.
- **Required layout**: src-layout (library code under `src/`) and
  `pyproject.toml` at repo root — the cache hash depends on these paths.
- **Call site example** — what statista's workflow collapses to:

  ```yaml
  - uses: serapeum-org/github-actions/actions/mkdocs-deploy@mkdocs-deploy/v2
    with:
      trigger: 'main'
      package-manager: 'uv'
      python-version: '3.12'
      install-groups: 'groups: docs'
      deploy-token: ${{ secrets.ACTIONS_DEPLOY_TOKEN }}
      notebooks-path: 'docs/notebook'
  ```

### Tests

- **Fixture**: `tests/data/mkdocs-deploy/with-notebooks/` — minimal
  `pyproject.toml` with a docs group including jupyter deps, one trivial
  `docs/notebook/hello.ipynb`, `mkdocs.yml` with `mkdocs-jupyter`
  `execute: false`.
- **Workflow**: `.github/workflows/test-mkdocs-deploy-notebooks.yml` — runs
  the action with `notebooks-path: 'docs/notebook'` twice in sequence (miss
  then hit) and asserts the notebook has outputs after each run. Matrix over
  `uv` / `pip` / `pixi`.

## Things to verify before implementing

- **`hashFiles(format(...), 'src/**/*.py', 'pyproject.toml')`** — verify the
  `format()` interpolation composes with `hashFiles()` inside a composite
  action step. If not, fall back to computing the hash in a prior shell step
  and passing it through a step output.
- **`github.action_path`** on a composite action consumed remotely via
  `@mkdocs-deploy/v1` — confirm the vendored script is reachable that way.
  Expected to work; smoke-test with the new fixture.
- **`uv run python script.py`** needs `pyproject.toml` in the working dir
  and must be able to import the library from inside the notebook. Should
  work after checkout, but verify in the fixture test.
- **`workflow_run` ref handling** — statista's release job pins
  `ref: github.event.workflow_run.head_branch` so checkout picks up the
  post-bump commits. That logic is caller-side and should NOT be absorbed
  into the action.

## Open questions

- Should we also expose `mkdocs-jupyter`'s `execute: false` as action-managed,
  or is configuration-as-code in `mkdocs.yml` the right seam? (Current
  answer: leave it in `mkdocs.yml`, just document the requirement.)
- Do we want a `strip-outputs-on-commit` pre-commit hook shipped alongside,
  or is that out of scope for an action repo? (Current answer: out of scope.)
