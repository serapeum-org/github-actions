# PyPI Release Action — Detailed Examples

Comprehensive examples for every input, package manager, and scenario supported by the PyPI
release composite action.

## Table of Contents

- [Basic Examples](#basic-examples)
- [Package Manager Examples](#package-manager-examples)
- [Repository URL Examples](#repository-url-examples)
- [Install Groups Examples](#install-groups-examples)
- [Verify Lock Examples](#verify-lock-examples)
- [Skip Publish Examples](#skip-publish-examples)
- [Complete Workflow Examples](#complete-workflow-examples)
- [Edge Cases and Special Scenarios](#edge-cases-and-special-scenarios)

---

## Basic Examples

### Minimal Configuration (uv, official PyPI)

The simplest publish workflow using all defaults:

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
        uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1
        with:
          pypi-username: __token__
          pypi-password: ${{ secrets.PYPI_API_TOKEN }}
```

**Behavior:**
- Package manager: uv (default)
- Python version: 3.12 (default)
- No extra dependency groups installed
- Lock file verification enabled
- Publishes to official PyPI

**Required project files:**

```toml
# pyproject.toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-package"
version = "1.0.0"
requires-python = ">=3.10"

[tool.hatch.build.targets.sdist]
include = ["src/", "README.md", "pyproject.toml"]
```

```
uv.lock        ← committed lock file (uv lock)
src/
  my_package/
    __init__.py
```

---

## Package Manager Examples

### pip

```yaml
- name: Checkout repository
  uses: actions/checkout@v5

- name: Publish to PyPI with pip
  uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1
  with:
    pypi-username: __token__
    pypi-password: ${{ secrets.PYPI_API_TOKEN }}
    package-manager: 'pip'
    python-version: '3.12'
```

**How it works:**
- Installs Python with pip and `pyproject.toml` dependencies
- Installs `build` and `twine` into the environment
- Builds with `python -m build`
- Publishes with `twine upload dist/*`

**No lock file required** — pip resolves dependencies at install time.

**Project setup:**

```toml
[project]
name = "my-package"
version = "1.0.0"
dependencies = ["requests>=2.28.0"]

[project.optional-dependencies]
dev = ["pytest>=7.0.0"]
```

---

### uv (Recommended)

```yaml
- name: Checkout repository
  uses: actions/checkout@v5

- name: Publish to PyPI with uv
  uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1
  with:
    pypi-username: __token__
    pypi-password: ${{ secrets.PYPI_API_TOKEN }}
    package-manager: 'uv'
    python-version: '3.12'
```

**How it works:**
- Installs Python and uv
- Syncs the environment from the committed `uv.lock`
- Builds with `uv build`
- Publishes with `uvx twine upload dist/*`

**Commit the lock file before your first CI run:**

```bash
uv lock
git add uv.lock
git commit -m "chore: add uv.lock"
```

**Project setup:**

```toml
[dependency-groups]
dev = ["pytest>=7.0.0"]
```

---

### pixi

```yaml
- name: Checkout repository
  uses: actions/checkout@v5

- name: Publish to PyPI with pixi
  uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1
  with:
    pypi-username: __token__
    pypi-password: ${{ secrets.PYPI_API_TOKEN }}
    package-manager: 'pixi'
    python-version: '3.12'
```

**How it works:**
- Installs pixi and activates the default environment
- Builds with `pixi run -e default python -m build`
- Publishes with `pixi run -e default twine upload dist/*`

**The pixi environment must include `build` and `twine`:**

```toml
# pixi.toml
[project]
name = "my-package"
channels = ["conda-forge"]
platforms = ["linux-64", "osx-arm64", "osx-64", "win-64"]

[feature.dev.dependencies]
python = "3.12.*"
python-build = "*"
twine = "*"

[environments]
default = ["dev"]
```

**Commit the lock file:**

```bash
pixi install
git add pixi.lock
git commit -m "chore: add pixi.lock"
```

---

## Repository URL Examples

### Official PyPI (default)

Leave `pypi-repository-url` empty (or omit it entirely):

```yaml
- uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1
  with:
    pypi-username: __token__
    pypi-password: ${{ secrets.PYPI_API_TOKEN }}
    # pypi-repository-url not set → uploads to https://pypi.org
```

---

### TestPyPI

Use TestPyPI to validate the full build-and-publish pipeline without affecting the production index:

```yaml
- uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1
  with:
    pypi-username: __token__
    pypi-password: ${{ secrets.TEST_PYPI_TOKEN }}
    pypi-repository-url: 'https://test.pypi.org/legacy/'
```

**Token scope note:**
- First-ever upload of a new package: token must be scoped to **All projects**
- Subsequent uploads: a token scoped to the specific project is sufficient

Manage TestPyPI tokens at: <https://test.pypi.org/manage/account/token/>

**Versioning tip:** Publish dev releases to avoid version conflicts across CI runs:

```yaml
- name: Set unique dev version
  run: |
    VERSION="0.0.dev${{ github.run_number }}"
    sed -i "s/version = \"0.1.0\"/version = \"$VERSION\"/" pyproject.toml

- uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1
  with:
    pypi-username: __token__
    pypi-password: ${{ secrets.TEST_PYPI_TOKEN }}
    pypi-repository-url: 'https://test.pypi.org/legacy/'
    verify-lock: 'false'   # lock is stale after version patch
```

---

### Custom / Private Index

Use any PEP 503-compatible index (e.g., AWS CodeArtifact, Nexus, Artifactory):

```yaml
- uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1
  with:
    pypi-username: ${{ secrets.PRIVATE_INDEX_USER }}
    pypi-password: ${{ secrets.PRIVATE_INDEX_TOKEN }}
    pypi-repository-url: 'https://my-company.example.com/simple/'
```

---

## Install Groups Examples

### Core dependencies only (empty string)

No extra groups are installed — only the project's `dependencies`:

```yaml
- uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1
  with:
    pypi-username: __token__
    pypi-password: ${{ secrets.PYPI_API_TOKEN }}
    install-groups: ''   # default — may be omitted
```

---

### Install a PEP 735 dependency group (uv)

```yaml
- uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1
  with:
    pypi-username: __token__
    pypi-password: ${{ secrets.PYPI_API_TOKEN }}
    package-manager: 'uv'
    install-groups: 'groups: dev'
```

**`pyproject.toml`:**

```toml
[dependency-groups]
dev = ["pytest>=7.0.0", "mypy>=1.0.0"]
```

---

### Install multiple dependency groups (uv)

```yaml
install-groups: 'groups: dev lint'
```

**`pyproject.toml`:**

```toml
[dependency-groups]
dev  = ["pytest>=7.0.0"]
lint = ["black>=23.0.0", "ruff>=0.1.0"]
```

---

### Install optional extras (pip/uv)

```yaml
install-groups: 'extras: viz'
```

**`pyproject.toml`:**

```toml
[project.optional-dependencies]
viz = ["matplotlib>=3.5.0", "plotly>=5.0.0"]
```

---

### Combine groups and extras (uv)

```yaml
install-groups: 'groups: dev, extras: viz'
```

---

### Named pixi environment

When using pixi, `install-groups` selects which pixi environment is activated and used for
building and publishing:

```yaml
- uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1
  with:
    pypi-username: __token__
    pypi-password: ${{ secrets.PYPI_API_TOKEN }}
    package-manager: 'pixi'
    install-groups: 'release'   # activates the 'release' environment
```

**`pixi.toml`:**

```toml
[feature.release.dependencies]
python = "3.12.*"
python-build = "*"
twine = "*"

[environments]
default = ["release"]
release = ["release"]
```

> **Important:** The selected environment must include `python-build` and `twine`.

---

## Verify Lock Examples

### verify-lock='true' (default — recommended for production)

Ensures the lock file exactly matches `pyproject.toml` before installing:

```yaml
- uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1
  with:
    pypi-username: __token__
    pypi-password: ${{ secrets.PYPI_API_TOKEN }}
    verify-lock: 'true'   # default — may be omitted
```

If the lock is stale, the job fails with a clear error message. Fix by running `uv lock` (or
`pixi install`) locally and committing the updated lock file.

---

### verify-lock='false' (skip check)

Useful in CI when the lock file is generated on-the-fly (e.g., after patching the version):

```yaml
- name: Generate fresh lock after version patch
  run: uv lock

- uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1
  with:
    pypi-username: __token__
    pypi-password: ${{ secrets.PYPI_API_TOKEN }}
    verify-lock: 'false'
```

> `verify-lock` applies only to uv and pixi. For pip there is no lock file mechanism.

---

## Skip Publish Examples

`skip-publish='true'` builds the package but does **not** upload it. Use this in CI to validate
the build pipeline without consuming TestPyPI quota or requiring credentials.

### Build-only check (no credentials needed)

```yaml
- name: Checkout repository
  uses: actions/checkout@v5

- name: Validate build
  uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1
  with:
    pypi-username: __token__
    pypi-password: unused-in-build-only-mode
    package-manager: 'uv'
    python-version: '3.12'
    verify-lock: 'false'
    skip-publish: 'true'

- name: Verify dist artifacts
  run: ls dist/*.whl dist/*.tar.gz
```

---

### Build matrix across package managers

```yaml
name: Validate build

on: [push, pull_request]

jobs:
  build:
    strategy:
      matrix:
        package-manager: [pip, uv, pixi]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5

      - uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1
        with:
          pypi-username: __token__
          pypi-password: unused
          package-manager: ${{ matrix.package-manager }}
          python-version: '3.12'
          verify-lock: 'false'
          skip-publish: 'true'
```

---

### Build matrix across Python versions

```yaml
name: Build on all supported Python versions

on: [push]

jobs:
  build:
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12', '3.13']
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5

      - uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1
        with:
          pypi-username: __token__
          pypi-password: unused
          package-manager: 'uv'
          python-version: ${{ matrix.python-version }}
          verify-lock: 'false'
          skip-publish: 'true'
```

---

### Cross-platform build validation

```yaml
name: Cross-platform build

on: [push]

jobs:
  build:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v5

      - uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1
        with:
          pypi-username: __token__
          pypi-password: unused
          package-manager: 'uv'
          python-version: '3.12'
          verify-lock: 'false'
          skip-publish: 'true'

      - name: Verify artifacts
        shell: bash
        run: ls dist/*.whl dist/*.tar.gz
```

---

## Complete Workflow Examples

### Publish on GitHub Release (uv)

The canonical production workflow — triggers when a GitHub release is published:

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
        uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1
        with:
          pypi-username: __token__
          pypi-password: ${{ secrets.PYPI_API_TOKEN }}
          package-manager: 'uv'
          python-version: '3.12'
```

---

### Publish on GitHub Release (pip)

```yaml
name: Publish to PyPI (pip)

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

      - uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1
        with:
          pypi-username: __token__
          pypi-password: ${{ secrets.PYPI_API_TOKEN }}
          package-manager: 'pip'
          python-version: '3.12'
```

---

### Publish on GitHub Release (pixi)

```yaml
name: Publish to PyPI (pixi)

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

      - uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1
        with:
          pypi-username: __token__
          pypi-password: ${{ secrets.PYPI_API_TOKEN }}
          package-manager: 'pixi'
          python-version: '3.12'
```

---

### GitHub Release + PyPI publish in sequence

Use the `release/github` action to create the release, then publish to PyPI:

```yaml
name: Release and Publish

on:
  workflow_dispatch:
    inputs:
      increment:
        description: 'Version increment'
        required: true
        type: choice
        options: [patch, minor, major]
        default: patch

permissions:
  contents: write

jobs:
  github-release:
    runs-on: ubuntu-latest
    steps:
      - uses: serapeum-org/github-actions/actions/release/github@release-github/v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          increment: ${{ inputs.increment }}

  pypi-publish:
    needs: github-release
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
        with:
          # Pull the version bump commit pushed by the release action
          ref: main

      - uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1
        with:
          pypi-username: __token__
          pypi-password: ${{ secrets.PYPI_API_TOKEN }}
          package-manager: 'uv'
          verify-lock: 'false'   # lock was regenerated by release action
```

---

### Test on PR, publish on merge to main

Validate the build on every PR; publish to PyPI only when merging to main:

```yaml
name: CI / CD

on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read

jobs:
  build-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5

      - uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1
        with:
          pypi-username: __token__
          pypi-password: unused
          skip-publish: 'true'
          verify-lock: 'false'

  publish:
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    needs: build-check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5

      - uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1
        with:
          pypi-username: __token__
          pypi-password: ${{ secrets.PYPI_API_TOKEN }}
```

---

### Publish with install groups (uv, groups + extras)

Install extra dependency groups needed for pre-build steps (e.g., code generation):

```yaml
- uses: actions/checkout@v5

- uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1
  with:
    pypi-username: __token__
    pypi-password: ${{ secrets.PYPI_API_TOKEN }}
    package-manager: 'uv'
    install-groups: 'groups: dev, extras: viz'
```

**`pyproject.toml`:**

```toml
[dependency-groups]
dev = ["pytest>=7.0.0", "mypy>=1.0.0"]

[project.optional-dependencies]
viz = ["matplotlib>=3.5.0"]
```

---

### TestPyPI smoke-test on every push to main

Publish a dev release to TestPyPI on every push to validate the publish pipeline continuously:

```yaml
name: Smoke-test publish (TestPyPI)

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read

jobs:
  test-publish-uv:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5

      - name: Stamp unique dev version
        run: |
          VERSION="0.0.dev${{ github.run_number }}"
          sed -i "s/version = \".*\"/version = \"$VERSION\"/" pyproject.toml

      - name: Regenerate lock after version patch
        uses: astral-sh/setup-uv@v4
        with:
          enable-cache: false

      - run: uv lock

      - uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1
        with:
          pypi-username: __token__
          pypi-password: ${{ secrets.TEST_PYPI_TOKEN }}
          package-manager: 'uv'
          pypi-repository-url: 'https://test.pypi.org/legacy/'
          verify-lock: 'false'

  test-publish-pip:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5

      - name: Stamp unique dev version (distinct base to avoid collision with uv job)
        run: |
          VERSION="0.1.dev${{ github.run_number }}"
          sed -i "s/version = \".*\"/version = \"$VERSION\"/" pyproject.toml

      - uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1
        with:
          pypi-username: __token__
          pypi-password: ${{ secrets.TEST_PYPI_TOKEN }}
          package-manager: 'pip'
          pypi-repository-url: 'https://test.pypi.org/legacy/'

  test-publish-pixi:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5

      - name: Stamp unique dev version (distinct base)
        run: |
          VERSION="0.2.dev${{ github.run_number }}"
          sed -i "s/version = \".*\"/version = \"$VERSION\"/" pyproject.toml

      - uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1
        with:
          pypi-username: __token__
          pypi-password: ${{ secrets.TEST_PYPI_TOKEN }}
          package-manager: 'pixi'
          pypi-repository-url: 'https://test.pypi.org/legacy/'
          verify-lock: 'false'
```

> **Version base strategy:** When running pip, uv, and pixi publish jobs in parallel for the
> same `run_number`, each must use a different version base (e.g., `0.0`, `0.1`, `0.2`) so that
> the filenames uploaded to TestPyPI are distinct. Both `N.N.devN` forms are valid PEP 440.

---

## Workspace / Monorepo Examples

### Build a specific workspace member (uv)

For a uv workspace where multiple packages live under `packages/`:

```yaml
- uses: actions/checkout@v5

- uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1
  with:
    pypi-username: __token__
    pypi-password: ${{ secrets.PYPI_API_TOKEN }}
    package-manager: 'uv'
    package: 'serapeum-ollama'
```

Uses `uv build --package serapeum-ollama` — uv resolves the workspace member by name natively.

**Workspace `pyproject.toml`:**

```toml
[tool.uv.workspace]
members = ["packages/*"]
```

---

### Build a specific workspace member (pip)

```yaml
- uses: actions/checkout@v5

- uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1
  with:
    pypi-username: __token__
    pypi-password: ${{ secrets.PYPI_API_TOKEN }}
    package-manager: 'pip'
    package: 'serapeum-core'
```

The action locates `packages/serapeum-core/pyproject.toml` (by matching `name = "serapeum-core"`)
and runs `python -m build packages/serapeum-core/ --outdir dist/`.

---

### Build a specific workspace member (pixi)

```yaml
- uses: actions/checkout@v5

- uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1
  with:
    pypi-username: __token__
    pypi-password: ${{ secrets.PYPI_API_TOKEN }}
    package-manager: 'pixi'
    package: 'serapeum-core'
```

Same directory-discovery as pip, but the build runs inside the pixi environment:
`pixi run -e default python -m build packages/serapeum-core/ --outdir dist/`.

---

### Publish all workspace members in a matrix

```yaml
name: Publish workspace packages

on:
  release:
    types: [published]

permissions:
  contents: read

jobs:
  publish:
    strategy:
      matrix:
        package:
          - serapeum-core
          - serapeum-ollama
          - serapeum-openai
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5

      - uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1
        with:
          pypi-username: __token__
          pypi-password: ${{ secrets.PYPI_API_TOKEN }}
          package-manager: 'uv'
          package: ${{ matrix.package }}
```

Each job builds and publishes exactly one package from the workspace. Because each matrix job
operates independently, packages are published in parallel.

---

## Edge Cases and Special Scenarios

### First-ever publish of a new package

**Situation:** The package has never been published to PyPI before.

**Requirement:** Your API token must have **All projects** scope. Project-scoped tokens cannot
create packages that do not yet exist on PyPI.

```yaml
# Use a broadly-scoped token for the first upload only.
# After the package exists, switch to a project-scoped token.
- uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1
  with:
    pypi-username: __token__
    pypi-password: ${{ secrets.PYPI_ALL_PROJECTS_TOKEN }}
```

---

### Prevent large sdist from workspace files

**Problem:** Running `python -m build` (pip/pixi) from a GitHub Actions workspace root causes
hatchling to bundle all repository files into the sdist, producing archives that are hundreds of
kilobytes larger than expected.

**Fix:** Add an explicit `include` list to `pyproject.toml`:

```toml
[tool.hatch.build.targets.sdist]
include = [
    "src/",
    "README.md",
    "pyproject.toml",
]
```

This is a no-op for local development (the project directory is clean) and prevents workspace
pollution in CI.

---

### Publish only when a Git tag is pushed

```yaml
name: Publish on tag push

on:
  push:
    tags:
      - 'v*'   # matches v1.0.0, v2.3.4-rc1, etc.

permissions:
  contents: read

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5

      - uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1
        with:
          pypi-username: __token__
          pypi-password: ${{ secrets.PYPI_API_TOKEN }}
```

---

### Publish to both PyPI and TestPyPI

```yaml
name: Dual publish

on:
  release:
    types: [published]

jobs:
  publish-testpypi:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1
        with:
          pypi-username: __token__
          pypi-password: ${{ secrets.TEST_PYPI_TOKEN }}
          pypi-repository-url: 'https://test.pypi.org/legacy/'

  publish-pypi:
    needs: publish-testpypi   # Only publish to production if TestPyPI succeeds
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1
        with:
          pypi-username: __token__
          pypi-password: ${{ secrets.PYPI_API_TOKEN }}
```

---

### Verify lock='true' with a freshly generated lock

In test workflows where no lock file is committed, generate one first:

```yaml
- uses: actions/checkout@v5

- name: Generate fresh uv lock
  uses: astral-sh/setup-uv@v4
  with:
    enable-cache: false

- run: uv lock

- uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1
  with:
    pypi-username: __token__
    pypi-password: unused
    verify-lock: 'true'   # now consistent — lock was just generated
    skip-publish: 'true'
```

---

### Custom Python version

```yaml
- uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1
  with:
    pypi-username: __token__
    pypi-password: ${{ secrets.PYPI_API_TOKEN }}
    python-version: '3.11'
```

All Python versions supported by `actions/setup-python` are accepted. The version is passed
through to the underlying `python-setup` action.

---

## Best Practices Summary

### 1. Always checkout before invoking the action

```yaml
- uses: actions/checkout@v5
- uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1
  with: ...
```

### 2. Use token authentication

```yaml
pypi-username: __token__
pypi-password: ${{ secrets.PYPI_API_TOKEN }}
```

Never store credentials in plaintext in workflow files.

### 3. Restrict sdist to project files

```toml
[tool.hatch.build.targets.sdist]
include = ["src/", "README.md", "pyproject.toml"]
```

### 4. Commit your lock file

```bash
uv lock && git add uv.lock && git commit -m "chore: update uv.lock"
```

A committed lock file ensures fully reproducible builds and enables `verify-lock='true'`.

### 5. Use distinct version bases for parallel TestPyPI jobs

When running multiple package managers in a matrix against TestPyPI, give each a unique minor
version to avoid filename collisions:

| Package manager | Version base |
|-----------------|-------------|
| uv | `0.0.devN` |
| pip | `0.1.devN` |
| pixi | `0.2.devN` |

### 6. Validate on PRs, publish on release

Use `skip-publish: 'true'` in PR checks to catch build failures early without consuming
PyPI quota or requiring secrets.

### 7. Pin action versions

```yaml
# Specific version — no surprise updates
uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1.0.0

# Major version — receives compatible updates automatically
uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1
```

---

## Additional Resources

- [Action Source Code](../../../actions/release/pypi/action.yml)
- [Test Workflows](../../../.github/workflows/test-release-pypi.yml)
- [PyPI Token Documentation](https://pypi.org/help/#apitoken)
- [TestPyPI](https://test.pypi.org/)
- [twine Documentation](https://twine.readthedocs.io/)
- [PEP 440 — Version Identifiers](https://peps.python.org/pep-0440/)
- [PEP 735 — Dependency Groups](https://peps.python.org/pep-0735/)
