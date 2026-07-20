# PyPI Release Action

Build and publish Python packages to PyPI (or TestPyPI) with support for multiple package managers.

## Overview

This composite action streamlines the PyPI release process by:

- **Building distribution artifacts** (wheel + sdist) using the configured package manager
- **Publishing to PyPI** (or any compatible index) via twine
- **Supporting multiple package managers**: pip, uv, pixi
- **Forwarding dependency groups** to the underlying python-setup actions for full environment control
- **Verifying lock file freshness** before installation (uv and pixi, optional)

> **Important:** This action does **not** checkout the repository. The calling workflow must run
> `actions/checkout` before invoking this action.

## Quick Start

### Basic Usage (uv)

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

permissions:
  contents: read

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v5

      - name: Publish to PyPI
        uses: serapeum-org/github-actions/actions/release/pypi@pypi-release/v1
        with:
          pypi-username: __token__
          pypi-password: ${{ secrets.PYPI_API_TOKEN }}
```

### With Explicit Configuration

```yaml
- name: Publish to PyPI
  uses: serapeum-org/github-actions/actions/release/pypi@pypi-release/v1
  with:
    pypi-username: __token__
    pypi-password: ${{ secrets.PYPI_API_TOKEN }}
    package-manager: 'uv'
    python-version: '3.12'
    install-groups: 'groups: dev'
    verify-lock: 'true'
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `pypi-username` | PyPI username. Use `__token__` when authenticating with an API token | ✅ Yes | - |
| `pypi-password` | PyPI password or API token value | ✅ Yes | - |
| `python-version` | Python version for building and publishing | No | `3.12` |
| `package-manager` | Package manager: `pip`, `uv`, `pixi` | No | `uv` |
| `install-groups` | Dependency groups or environments to install (see below) | No | `''` |
| `pypi-repository-url` | Custom index URL. Leave empty for official PyPI | No | `''` |
| `verify-lock` | Verify lock file is up to date before installing (uv/pixi only) | No | `'true'` |
| `package` | Workspace member name to build. Leave empty for single-package repos | No | `''` |
| `skip-publish` | Skip the publish step — build only. **Testing only.** | No | `'false'` |

### Install Groups Format

The `install-groups` input format varies by package manager:

**For pip/uv:**
- `"groups: dev test"` — Install PEP 735 dependency groups
- `"extras: aws viz"` — Install optional dependencies
- `"groups: dev, extras: aws"` — Combine both
- `""` — Install only core dependencies

**For pixi:**
- `"default"` — Use default pixi environment
- `"py312"` — Named environment
- The named environment must include `build` and `twine`

### `package` — Workspace Member Builds

Set `package` to the package **name** (the `[project] name` value in `pyproject.toml`) to build
only that member of a multi-package workspace:

```yaml
- uses: serapeum-org/github-actions/actions/release/pypi@pypi-release/v1
  with:
    pypi-username: __token__
    pypi-password: ${{ secrets.PYPI_API_TOKEN }}
    package: 'serapeum-ollama'
```

Leave `package` empty (the default) for single-package repositories.

**How the package directory is resolved (pip and pixi):**

The action runs:
```bash
find . -not -path './.git/*' -name "pyproject.toml" \
  | xargs grep -l 'name = "serapeum-ollama"' | head -1 | xargs dirname
```
It then passes that directory to `python -m build <dir> --outdir dist/`, so artifacts always
land in the workspace-level `dist/` directory.

**uv** resolves the package natively via `uv build --package <name>` — no directory search
needed.

### `pypi-repository-url`

| Value | Destination |
|-------|-------------|
| (empty) | Official PyPI (`https://pypi.org`) |
| `https://test.pypi.org/legacy/` | TestPyPI |
| Any compliant URL | Custom index |

### `verify-lock`

Controls lock file freshness checking (uv and pixi only):

- `'true'` (default) — Runs `uv sync --frozen` / `pixi install --frozen`; fails if lock is stale
- `'false'` — Skips the check; useful when the lock is generated on-the-fly in CI

## Prerequisites

### Caller Responsibilities

The calling workflow must:

1. **Checkout the repository** before invoking this action:

   ```yaml
   - uses: actions/checkout@v5
   ```

2. **Provide valid credentials** via secrets:

   ```yaml
   with:
     pypi-username: __token__
     pypi-password: ${{ secrets.PYPI_API_TOKEN }}
   ```

### Token Scope on PyPI / TestPyPI

| Situation | Required token scope |
|-----------|---------------------|
| First-ever upload of a new package | **All projects** |
| Subsequent uploads | Project-scoped (e.g., scoped to `my-package`) |

Create and manage tokens at:
- PyPI: <https://pypi.org/manage/account/token/>
- TestPyPI: <https://test.pypi.org/manage/account/token/>

### Required Files in the Repository

- **`pyproject.toml`** — package metadata (name, version, build-system)
- **`uv.lock`** (uv only) — committed lock file, required when `verify-lock='true'`
- **`pixi.lock`** (pixi only) — committed lock file, required when `verify-lock='true'`
- **`pixi.toml`** (pixi only) — must declare an environment that includes `build` and `twine`

### Minimal `pyproject.toml`

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-package"
version = "1.0.0"
requires-python = ">=3.10"

[tool.hatch.build.targets.wheel]
packages = ["src/my_package"]

# Recommended: restrict sdist to project files only
[tool.hatch.build.targets.sdist]
include = [
    "src/",
    "README.md",
    "pyproject.toml",
]
```

> **Tip:** Always set `[tool.hatch.build.targets.sdist] include` when running in a GitHub Actions
> workspace. Without it, hatchling includes every file in the working directory, which can
> produce unexpectedly large sdist archives.

## How It Works

### Build & Publish Flow

1. **Display configuration** — Logs inputs for debugging (credentials are never printed)
2. **Set up Python environment** — Delegates to the appropriate `python-setup` action:
   - `pip` → `actions/python-setup/pip@pip/v1.1.0`
   - `uv` → `actions/python-setup/uv@uv/v1.2.0`
   - `pixi` → `actions/python-setup/pixi@pixi/v1.2.0`
3. **Install build tools** (pip only) — `pip install build twine`
4. **Build package** — Produces `dist/*.whl` and `dist/*.tar.gz`
5. **Publish to PyPI** — Uploads all artifacts in `dist/` via twine (skipped when `skip-publish='true'`)
6. **Summary** — Prints a release summary to the workflow log

### Build Commands by Package Manager

| Package Manager | Single-package repo | Workspace (with `package` input) |
|-----------------|---------------------|----------------------------------|
| `pip` | `python -m build` | `python -m build <pkg_dir> --outdir dist/` |
| `uv` | `uv build` | `uv build --package <name>` |
| `pixi` | `pixi run -e <env> python -m build` | `pixi run -e <env> python -m build <pkg_dir> --outdir dist/` |

For pip and pixi, the package directory is discovered automatically by searching all
`pyproject.toml` files in the workspace for `name = "<package>"`.

> **Note:** `--outdir dist/` ensures workspace-member builds place artifacts in the root-level
> `dist/` directory regardless of where the sub-package lives in the tree.

### Publish Commands by Package Manager

| Package Manager | Publish Command |
|-----------------|-----------------|
| `pip` | `twine upload [--repository-url URL] dist/*` |
| `uv` | `uvx twine upload [--repository-url URL] dist/*` |
| `pixi` | `pixi run -e <env> twine upload [--repository-url URL] dist/*` |

## Permissions

This action requires no elevated permissions — it does not push to git or create GitHub releases.

```yaml
permissions:
  contents: read
```

## Common Patterns

### Publish on GitHub Release

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

permissions:
  contents: read

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5

      - uses: serapeum-org/github-actions/actions/release/pypi@pypi-release/v1
        with:
          pypi-username: __token__
          pypi-password: ${{ secrets.PYPI_API_TOKEN }}
```

### Combine GitHub Release + PyPI Publish

```yaml
name: Release and Publish

on:
  workflow_dispatch:
    inputs:
      increment:
        type: choice
        options: [patch, minor, major]
        default: patch

permissions:
  contents: write

jobs:
  github-release:
    runs-on: ubuntu-latest
    steps:
      - uses: serapeum-org/github-actions/actions/release/github@github-release/v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          increment: ${{ inputs.increment }}

  pypi-publish:
    needs: github-release
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5

      - uses: serapeum-org/github-actions/actions/release/pypi@pypi-release/v1
        with:
          pypi-username: __token__
          pypi-password: ${{ secrets.PYPI_API_TOKEN }}
```

## Troubleshooting

### 403 Forbidden on First Upload

**Cause:** You are using a project-scoped token but the package does not yet exist on PyPI/TestPyPI.

**Solution:** Use an "All projects" scoped token for the first upload. Afterwards, a project-scoped token is sufficient.

### 400 Bad Request — Version Already Exists

**Cause:** The version in `pyproject.toml` was already uploaded.

**Solution:** Bump the version in `pyproject.toml` (and regenerate `uv.lock` if using uv) before publishing.

### Large sdist (unexpected files in archive)

**Cause:** No `include` list in `[tool.hatch.build.targets.sdist]`. Hatchling includes every file visible from the working directory — in CI this includes the entire repository checkout.

**Solution:** Add an explicit `include` list:

```toml
[tool.hatch.build.targets.sdist]
include = [
    "src/",
    "README.md",
    "pyproject.toml",
]
```

### Package Not Found in Workspace

**Error:** `Package 'my-pkg' not found in workspace (no pyproject.toml with name = "my-pkg")`

**Cause:** The `package` input was set but no `pyproject.toml` in the workspace contains
`name = "my-pkg"` (applies to pip and pixi only).

**Solution:** Verify the package name matches the `[project] name` exactly:

```bash
grep -r 'name = ' packages/*/pyproject.toml
```

Then use that exact string as the `package` input. Names are case-sensitive and must include
hyphens/underscores exactly as declared.

### Lock File Verification Failure

**Cause:** `verify-lock='true'` but the committed `uv.lock` or `pixi.lock` is out of date with `pyproject.toml`.

**Solution 1:** Regenerate and commit the lock file locally:

```bash
uv lock   # or: pixi install
git add uv.lock
git commit -m "chore: update uv.lock"
```

**Solution 2:** Disable verification (not recommended for production):

```yaml
verify-lock: 'false'
```

### pixi Environment Missing `build` or `twine`

**Cause:** The pixi environment passed via `install-groups` does not include the `python-build` and `twine` conda packages.

**Solution:** Add them to the environment in `pixi.toml`:

```toml
[feature.dev.dependencies]
python-build = "*"
twine = "*"

[environments]
default = ["dev"]
```

## Examples

See [EXAMPLES.md](./EXAMPLES.md) for comprehensive examples covering:

- All three package managers (pip, uv, pixi)
- Official PyPI and TestPyPI publishing
- Build-only mode (`skip-publish`)
- `install-groups` variations
- `verify-lock` behavior
- Multi-environment and cross-platform scenarios
- Full release pipeline integration

## Related Documentation

- [PyPI Token Documentation](https://pypi.org/help/#apitoken)
- [TestPyPI](https://test.pypi.org/)
- [twine Documentation](https://twine.readthedocs.io/)
- [uv Documentation](https://docs.astral.sh/uv/)
- [pixi Documentation](https://pixi.sh/)
- [PEP 440 — Version Identifiers](https://peps.python.org/pep-0440/)
- [PEP 735 — Dependency Groups](https://peps.python.org/pep-0735/)

## Support

For issues and feature requests, please use the [GitHub Issues](https://github.com/serapeum-org/github-actions/issues).
