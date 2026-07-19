# Python Setup with uv - Complete Guide

Composite GitHub Action for setting up Python environments with the uv package manager, designed for modern Python projects using `pyproject.toml` and dependency groups.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Inputs Reference](#inputs-reference)
- [Features](#features)
- [Usage Scenarios](#usage-scenarios)
- [Dependency Groups](#dependency-groups)
- [Lock File Verification](#lock-file-verification)
- [Virtual Environment](#virtual-environment)
- [Testing Guide](#testing-guide)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Overview

This action provides a complete Python environment setup using [uv](https://github.com/astral-sh/uv), the fast Python package installer and resolver. It automatically:

- Installs Python and uv
- Verifies lock file integrity (optional)
- Installs dependencies with group support
- Activates the virtual environment automatically
- Caches dependencies for faster CI runs

**Location**: `serapeum-org/github-actions/actions/python-setup/uv@v1`

## Quick Start

### Basic Usage (Core Dependencies Only)

```yaml
steps:
  - uses: actions/checkout@v5
  - uses: serapeum-org/github-actions/actions/python-setup/uv@v1

  # Virtual environment is automatically activated!
  - run: python --version
  - run: pytest
```

### With Dependency Groups

```yaml
steps:
  - uses: actions/checkout@v5
  - uses: serapeum-org/github-actions/actions/python-setup/uv@v1
    with:
      install-groups: 'dev test'

  - run: pytest
  - run: black --check .
```

## Inputs Reference

| Input | Description | Required | Default | Valid Values |
|-------|-------------|----------|---------|--------------|
| `python-version` | Python version to install | No | `'3.12'` | Any valid Python version (e.g., `'3.10'`, `'3.11'`, `'3.12'`) |
| `install-groups` | Dependency groups to install | No | `''` (core only) | Space or comma-separated list (e.g., `'dev'`, `'dev test'`, `'dev,test,docs'`) |
| `verify-lock` | Verify lock file is up to date | No | `'true'` | `'true'`, `'false'` |
| `version` | Version of uv to install | No | `''` (auto-resolve) | Version number (e.g., `'0.5.0'`), `'latest'`, or `''` |

### Input Details

#### `python-version`
Specifies which Python version to install via `actions/setup-python@v6`.

**Examples:**
```yaml
python-version: '3.10'  # Python 3.10
python-version: '3.11'  # Python 3.11
python-version: '3.12'  # Python 3.12 (default)
```

#### `install-groups`
Specifies which dependency groups from `[dependency-groups]` in `pyproject.toml` to install.

**Default behavior (`''`)**: Installs only core dependencies (those listed in `dependencies`), no optional groups.

**When specified**: Installs core dependencies + only the specified groups (all other groups are excluded).

**Formats supported:**
- Space-separated: `'dev test'`
- Comma-separated: `'dev,test,docs'`
- Mixed: `'dev, test docs'`

**Important**: The action uses `uv sync --no-default-groups --group <name>` to ensure ONLY the specified groups are installed, preventing unwanted transitive group installations.

#### `verify-lock`
Controls whether to verify the `uv.lock` file is up to date before installation.

**When `'true'` (default)**: Runs `uv lock --check` and fails if lock file is outdated.

**When `'false'`: Skips lock file verification.

#### `version`
Selects the uv release installed by `astral-sh/setup-uv` (forwarded as its `version` input).

**Default (`''`)**: Leaves the version unset, so setup-uv resolves it from `pyproject.toml`/`uv.toml`, falling back to `latest` — the same behavior as before this input existed.

**When specified**: Pins uv to the given release, or installs the newest with `'latest'`:

```yaml
# Pin a specific uv version (reproducible)
version: '0.5.0'

# Always use the newest uv release
version: 'latest'
```

**Note**: Use the version number without a leading `v` (e.g. `'0.5.0'`), matching setup-uv's own format.

## Features

### 1. Automatic Virtual Environment Activation

The action automatically activates the `.venv` virtual environment by:
- Adding `.venv/bin` (Linux/macOS) or `.venv/Scripts` (Windows) to `$GITHUB_PATH`
- Setting `$VIRTUAL_ENV` environment variable

**Result**: All subsequent steps can use `python`, `pytest`, `black`, etc. directly without manual activation or `uv run`.

```yaml
- uses: serapeum-org/github-actions/actions/python-setup/uv@v1
  with:
    install-groups: 'dev test'

# No activation needed!
- run: python --version  # Uses venv Python
- run: pytest            # Uses venv pytest
- run: black .           # Uses venv black
```

### 2. Smart Dependency Group Management

The action uses `--no-default-groups` flag to ensure clean group isolation:

```yaml
# pyproject.toml
[project]
dependencies = ["requests"]

[dependency-groups]
dev = ["httpx"]
test = ["pytest-cov"]
docs = ["mkdocs"]
```

**Without groups** (`install-groups: ''`):
- Command: `uv sync --frozen --no-default-groups`
- Installs: `requests` only

**With specific groups** (`install-groups: 'test docs'`):
- Command: `uv sync --frozen --no-default-groups --group test --group docs`
- Installs: `requests` + `pytest-cov` + `mkdocs`
- Excludes: `httpx` (dev group not requested)

### 3. Lock File Verification

Ensures reproducible builds by validating `uv.lock` matches `pyproject.toml`:

```yaml
- uses: serapeum-org/github-actions/actions/python-setup/uv@v1
  with:
    verify-lock: 'true'  # Fails if lock is outdated
```

**Skip verification** (useful for dynamic dependency updates):
```yaml
- uses: serapeum-org/github-actions/actions/python-setup/uv@v1
  with:
    verify-lock: 'false'
```

### 4. Dependency Caching

The action uses `astral-sh/setup-uv@v4` with:
```yaml
enable-cache: true
cache-dependency-glob: uv.lock
```

This caches dependencies based on `uv.lock` hash, significantly speeding up CI runs.

### 5. Comprehensive Logging

The action provides detailed output:
```
Environment information
  Virtual environment: ACTIVATED

  Virtual environment location:
    /home/runner/work/repo/repo/.venv

  Python executable:
    /home/runner/work/repo/repo/.venv/bin/python

  The virtual environment has been automatically activated.
  You can now use 'python' and installed CLI tools directly in subsequent steps.
```

## Usage Scenarios

### Scenario 1: Core Dependencies Only

**Use Case**: Simple project with only core dependencies, no dev tools needed.

```yaml
steps:
  - uses: actions/checkout@v5
  - uses: serapeum-org/github-actions/actions/python-setup/uv@v1

  - name: Run application
    run: python main.py
```

**pyproject.toml**:
```toml
[project]
name = "my-app"
version = "1.0.0"
dependencies = ["requests", "pydantic"]
```

**What gets installed**: `requests`, `pydantic` only

### Scenario 2: Development Environment

**Use Case**: Local-style development with all dev tools.

```yaml
steps:
  - uses: actions/checkout@v5
  - uses: serapeum-org/github-actions/actions/python-setup/uv@v1
    with:
      install-groups: 'dev'

  - run: black --check .
  - run: mypy src/
  - run: ruff check .
```

**pyproject.toml**:
```toml
[project]
dependencies = ["requests"]

[dependency-groups]
dev = ["black", "mypy", "ruff"]
```

**What gets installed**: `requests` + `black` + `mypy` + `ruff`

### Scenario 3: Testing Workflow

**Use Case**: Run tests without dev tools to match production environment.

```yaml
steps:
  - uses: actions/checkout@v5
  - uses: serapeum-org/github-actions/actions/python-setup/uv@v1
    with:
      install-groups: 'groups: test'

  - run: pytest --cov=src --cov-report=xml
  - run: coverage report
```

**pyproject.toml**:
```toml
[project]
dependencies = ["requests"]

[dependency-groups]
dev = ["black", "mypy"]
test = ["pytest", "pytest-cov", "coverage"]
```

**What gets installed**: `requests` + `pytest` + `pytest-cov` + `coverage` (dev tools excluded)

### Scenario 4: Documentation Build

**Use Case**: Build documentation without test/dev dependencies.

```yaml
steps:
  - uses: actions/checkout@v5
  - uses: serapeum-org/github-actions/actions/python-setup/uv@v1
    with:
      install-groups: 'docs'

  - run: mkdocs build
  - run: mkdocs gh-deploy --force
```

**pyproject.toml**:
```toml
[project]
dependencies = ["mylib"]

[dependency-groups]
docs = ["mkdocs", "mkdocs-material"]
```

**What gets installed**: `mylib` + `mkdocs` + `mkdocs-material`

### Scenario 5: Multiple Groups

**Use Case**: CI workflow that needs both testing and linting.

```yaml
steps:
  - uses: actions/checkout@v5
  - uses: serapeum-org/github-actions/actions/python-setup/uv@v1
    with:
      install-groups: 'dev test'

  - name: Lint
    run: |
      black --check .
      mypy src/

  - name: Test
    run: pytest --cov=src
```

**pyproject.toml**:
```toml
[project]
dependencies = ["requests"]

[dependency-groups]
dev = ["black", "mypy"]
test = ["pytest", "pytest-cov"]
docs = ["mkdocs"]  # Not installed
```

**What gets installed**: `requests` + `black` + `mypy` + `pytest` + `pytest-cov`

**What's excluded**: `mkdocs` (docs group not requested)

### Scenario 6: Matrix Testing Across Python Versions

**Use Case**: Test compatibility with multiple Python versions.

```yaml
strategy:
  matrix:
    python-version: ['3.10', '3.11', '3.12']

steps:
  - uses: actions/checkout@v5
  - uses: serapeum-org/github-actions/actions/python-setup/uv@v1
    with:
      python-version: ${{ matrix.python-version }}
      install-groups: 'groups: test'

  - run: pytest
```

**Result**: Tests run on Python 3.10, 3.11, and 3.12

### Scenario 7: Cross-Platform Testing

**Use Case**: Ensure application works on all major operating systems.

```yaml
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest, macos-latest]

steps:
  - uses: actions/checkout@v5
  - uses: serapeum-org/github-actions/actions/python-setup/uv@v1
    with:
      install-groups: 'test'

  - run: pytest
```

**Result**: Tests run on Linux, Windows, and macOS

### Scenario 8: Skip Lock Verification for Dynamic Dependencies

**Use Case**: Dependencies from Git branches or local paths that change frequently.

**pyproject.toml**:
```toml
[project]
dependencies = [
  "mylib @ git+https://github.com/user/repo@main",
  "another-lib @ git+https://github.com/user/another@develop"
]
```

**Workflow:**
```yaml
jobs:
  test-dynamic:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: serapeum-org/github-actions/actions/python-setup/uv@v1
        with:
          verify-lock: 'false'  # Skip lock check for dynamic deps
          install-groups: 'groups: dev'

      - name: Run tests
        run: pytest
```

**What Happens**:
- Skips `uv lock --check` validation
- Installs dependencies from lock file as-is
- Useful when lock file changes frequently

### Scenario 9: No Dependency Groups Section

**Use Case**: Simple project without optional dependency groups.

**pyproject.toml**:
```toml
[project]
name = "simple-app"
dependencies = ["requests", "click"]
# No [dependency-groups] section
```

**Workflow:**
```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: serapeum-org/github-actions/actions/python-setup/uv@v1

      - name: Run application
        run: python app.py
```

**What Happens**:
- Core dependencies installed: `requests`, `click`
- No error even though `[dependency-groups]` section doesn't exist
- Action handles missing dependency-groups gracefully

### Scenario 10: Multiple Formats for Groups

**Use Case**: Demonstrating flexible group specification formats.

**All these are equivalent:**

```yaml
# Space-separated
install-groups: 'groups: dev test docs'

# Comma-separated
install-groups: 'groups: dev,test,docs'

# Mixed
install-groups: 'groups: dev, test docs'
```

**Workflow:**
```yaml
jobs:
  test-formats:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        format:
          - 'groups: dev test docs'
          - 'groups: dev,test,docs'
          - 'groups: dev, test docs'
    steps:
      - uses: actions/checkout@v5
      - uses: serapeum-org/github-actions/actions/python-setup/uv@v1
        with:
          install-groups: ${{ matrix.format }}

      - name: Verify all formats work
        run: |
          python -c "import black, pytest, mkdocs"
          echo "[OK] All formats install same dependencies"
```

### Scenario 11: Complex Multi-Group Setup

**Use Case**: Large project with many specialized dependency groups.

**pyproject.toml**:
```toml
[project]
name = "enterprise-app"
dependencies = ["requests", "pydantic", "typer"]

[project.optional-dependencies]
aws = ["boto3", "s3fs"]
azure = ["azure-storage-blob", "azure-identity"]
gcp = ["google-cloud-storage"]
postgres = ["psycopg2-binary", "sqlalchemy"]
redis = ["redis", "hiredis"]

[dependency-groups]
dev = ["black", "mypy", "ruff", "ipython"]
test = ["pytest", "pytest-cov", "pytest-mock", "hypothesis"]
docs = ["mkdocs", "mkdocs-material", "mkdocstrings[python]"]
lint = ["pylint", "flake8", "bandit"]
build = ["build", "twine", "wheel"]
```

**Workflow (development):**
```yaml
jobs:
  develop:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: serapeum-org/github-actions/actions/python-setup/uv@v1
        with:
          install-groups: 'groups: dev test lint, extras: postgres redis'

      - name: Full dev environment
        run: |
          black --check .
          mypy src/
          pytest --cov=src
```

**Workflow (documentation):**
```yaml
jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: serapeum-org/github-actions/actions/python-setup/uv@v1
        with:
          install-groups: 'groups: docs'

      - name: Build docs
        run: mkdocs build
```

**Workflow (production):**
```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: serapeum-org/github-actions/actions/python-setup/uv@v1
        with:
          install-groups: 'extras: aws postgres'  # No dev groups

      - name: Deploy app
        run: python -m app
```

### Scenario 12: Testing Lock File Validation

**Use Case**: Ensuring lock file stays in sync with pyproject.toml.

**Workflow:**
```yaml
jobs:
  validate-lock:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      
      - name: Verify lock file is up to date
        uses: serapeum-org/github-actions/actions/python-setup/uv@v1
        with:
          verify-lock: 'true'  # Default, but explicit
          install-groups: 'groups: dev'

      - name: Run checks
        run: |
          echo "Lock file is valid and up to date"
          pytest
```

**What Happens**:
- Runs `uv lock --check` before installation
- **Fails if lock file is outdated** with clear error message
- Prevents deploying with mismatched dependencies

### Scenario 13: Explicit Dev Group Installation

**Use Case**: Ensuring dev tools are available for local-style development in CI.

**pyproject.toml**:
```toml
[project]
name = "myapp"
dependencies = ["fastapi", "uvicorn"]

[dependency-groups]
dev = ["pytest", "black", "mypy", "ruff", "httpx"]
```

**Workflow:**
```yaml
jobs:
  dev-ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: serapeum-org/github-actions/actions/python-setup/uv@v1
        with:
          install-groups: 'groups: dev'

      - name: Run all dev checks
        run: |
          black --check .
          mypy src/
          ruff check .
          pytest
```

**What Happens**:
- Core: `fastapi`, `uvicorn`
- Dev group: `pytest`, `black`, `mypy`, `ruff`, `httpx`
- All dev tools available for comprehensive CI checks

### Scenario 14: Minimal Production Build

**Use Case**: Production deployment with only runtime dependencies.

**pyproject.toml**:
```toml
[project]
name = "webapp"
dependencies = ["flask", "gunicorn", "psycopg2"]

[dependency-groups]
dev = ["pytest", "black"]
test = ["pytest-cov", "faker"]
```

**Workflow:**
```yaml
jobs:
  production:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: serapeum-org/github-actions/actions/python-setup/uv@v1
        # No install-groups = core only

      - name: Verify minimal install
        run: |
          uv pip list
          python -c "import flask, gunicorn, psycopg2"
          echo "[OK] Only production dependencies installed"

      - name: Deploy
        run: gunicorn app:app
```

**What Happens**:
- Only core dependencies installed
- No dev/test tools (smaller image, faster deployment)
- Production-ready minimal environment

### Scenario 15: Cache Behavior Testing

**Use Case**: Understanding and testing caching behavior.

**Workflow:**
```yaml
jobs:
  cache-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      
      - name: First run (populate cache)
        uses: serapeum-org/github-actions/actions/python-setup/uv@v1
        with:
          cache: 'true'  # Default
          install-groups: 'groups: dev test'

      - name: Verify packages
        run: uv pip list

      # On subsequent runs:
      # - Cache restored from uv.lock hash
      # - Much faster (seconds vs minutes)
```

**Cache behavior**:
- **First run**: Downloads and caches all dependencies (~2-5 minutes)
- **Subsequent runs**: Restores from cache (~10-30 seconds)
- **Cache key**: Based on `uv.lock` hash
- **Cache invalidation**: Automatic when `uv.lock` changes

## Dependency Groups

### Dependency Groups vs Optional Dependencies

**Key Differences**:

1. **Dependency Groups** (`[dependency-groups]`):
   - Part of PEP 735 standard
   - **Fully supported by uv** (unlike pip)
   - Development-only dependencies, not published with package
   - Installed using `--group` flag with `uv sync`
   - Use prefix `groups:` in this action
   - **Recommended for uv users**

2. **Optional Dependencies** (`[project.optional-dependencies]`):
   - Part of PEP 621 standard, widely supported
   - Published with your package, can be installed by end users
   - Installed using `--extra` flag with `uv sync`
   - Use prefix `extras:` in this action
   - **Also supported by uv**

**Key Advantage of uv**: Unlike pip, uv has **full native support** for PEP 735 dependency groups without any limitations or warnings.

### Understanding Dependency Groups

Dependency groups in `pyproject.toml` allow organizing optional dependencies:

```toml
[project]
name = "myapp"
dependencies = ["requests"]  # Core - always installed

[project.optional-dependencies]
aws = ["boto3", "s3fs"]      # Published extras (end-user features)
viz = ["matplotlib", "seaborn"]  # End-user features

[dependency-groups]
dev = ["black", "mypy", "ruff"]      # Development tools (not published)
test = ["pytest", "pytest-cov"]  # Testing tools (not published)
docs = ["mkdocs", "mkdocstrings"]  # Documentation tools (not published)
```

**When to use which:**
- `optional-dependencies`: Features for end-users (e.g., cloud integrations, visualization)
- `dependency-groups`: Development tools only needed by contributors (e.g., linting, testing)

### Group Installation Behavior

| `install-groups` Value | Command Generated | What Gets Installed |
|------------------------|-------------------|---------------------|
| `''` (empty/default) | `uv sync --frozen --no-default-groups` | Core only |
| `'groups: dev'` | `uv sync --frozen --no-default-groups --group dev` | Core + dev |
| `'groups: test'` | `uv sync --frozen --no-default-groups --group test` | Core + test |
| `'groups: dev test'` | `uv sync --frozen --no-default-groups --group dev --group test` | Core + dev + test |
| `'groups: dev,test,docs'` | `uv sync --frozen --no-default-groups --group dev --group test --group docs` | Core + dev + test + docs |
| `'extras: aws'` | `uv sync --frozen --no-default-groups --extra aws` | Core + aws extra |
| `'groups: dev, extras: aws'` | `uv sync --frozen --no-default-groups --group dev --extra aws` | Core + dev + aws |

### Why `--no-default-groups`?

By default, `uv sync` includes certain groups automatically (like `dev`). Using `--no-default-groups` ensures:
- ✅ **Clean group isolation** - only requested groups are installed
- ✅ **Predictable builds** - same result every time
- ✅ **Reproducible** - no unexpected transitive group installations
- ✅ **Explicit control** - you specify exactly what to install

**Without `--no-default-groups`** (old behavior):
```bash
uv sync --group test  # Might also install 'dev' group unexpectedly
```

**With `--no-default-groups`** (current behavior):
```bash
uv sync --no-default-groups --group test  # ONLY test group
```

### Format Options

The action accepts multiple formats for `install-groups`:

**Space-separated:**
```yaml
install-groups: 'groups: dev test docs'
```

**Comma-separated:**
```yaml
install-groups: 'groups: dev,test,docs'
```

**Mixed (spaces and commas):**
```yaml
install-groups: 'groups: dev, test docs'
```

**Groups and extras together:**
```yaml
install-groups: 'groups: dev test, extras: aws viz'
```

**Reverse order (extras first):**
```yaml
install-groups: 'extras: aws, groups: dev'
```

All formats produce the same result - the action parses them intelligently.

### Common Group Patterns

**Development:**
```toml
[dependency-groups]
dev = ["black>=23.0", "mypy>=1.0", "ruff>=0.1", "ipython>=8.0"]
```

```yaml
- uses: .../actions/python-setup/uv@v1
  with:
    install-groups: 'groups: dev'
- run: black --check .
- run: mypy src/
```

**Testing:**
```toml
[dependency-groups]
test = ["pytest>=7.0", "pytest-cov>=4.0", "pytest-mock>=3.0", "faker>=20.0"]
```

```yaml
- uses: .../actions/python-setup/uv@v1
  with:
    install-groups: 'groups: test'
- run: pytest --cov=src
```

**Documentation:**
```toml
[dependency-groups]
docs = ["mkdocs>=1.5", "mkdocs-material>=9.0", "mkdocstrings[python]>=0.24"]
```

```yaml
- uses: .../actions/python-setup/uv@v1
  with:
    install-groups: 'groups: docs'
- run: mkdocs build
```

**Production (extras for end-users):**
```toml
[project.optional-dependencies]
postgres = ["psycopg2-binary>=2.9"]
redis = ["redis>=5.0"]
```

```yaml
- uses: .../actions/python-setup/uv@v1
  with:
    install-groups: 'extras: postgres redis'
- run: python app.py
```

**Combined (dev + testing):**
```yaml
- uses: .../actions/python-setup/uv@v1
  with:
    install-groups: 'groups: dev test'
- run: black --check .
- run: pytest
```

**All groups:**
```yaml
- uses: .../actions/python-setup/uv@v1
  with:
    install-groups: 'groups: dev test docs, extras: aws azure'
```

### Installation Summary Output

The action provides detailed feedback about what will be installed:

**Example output:**
```
Processing install-groups: groups: dev test, extras: aws
  - Adding dependency group: dev
  - Adding dependency group: test
  - Adding optional dependency (extra): aws

=== Installation Summary ===
✓ Dependency groups will be installed: dev test
✓ Optional dependencies (extras) will be installed: aws
✗ No optional dependencies specified
✓ Core dependencies will always be installed
==========================

Running: uv sync --frozen --no-default-groups --group dev --group test --extra aws
```

This makes it clear exactly what's being installed and why.

## Lock File Verification

### What is Lock File Verification?

`uv.lock` is a lock file that pins exact versions of all dependencies. Verification ensures the lock file is synchronized with `pyproject.toml`.

### When to Enable (Default)

**Enable verification (`verify-lock: 'true'`) when:**
- Working in a team (ensure everyone uses same dependencies)
- Production deployments (reproducible builds)
- CI/CD pipelines (catch dependency drift early)

```yaml
- uses: serapeum-org/github-actions/actions/python-setup/uv@v1
  with:
    verify-lock: 'true'  # Fails if lock is outdated
```

**Error if outdated**:
```
error: The lockfile at `uv.lock` needs to be updated, but `--locked` was provided.
```

**Fix**: Run `uv lock` locally and commit the updated lock file.

### When to Disable

**Disable verification (`verify-lock: 'false'`) when:**
- Dependencies change frequently (Git dependencies)
- Development branches with experimental changes
- Prototyping/testing new dependencies

```yaml
- uses: serapeum-org/github-actions/actions/python-setup/uv@v1
  with:
    verify-lock: 'false'
```

### Lock File Workflow

**Recommended workflow**:
1. Modify `pyproject.toml` (add/update dependencies)
2. Run `uv lock` locally
3. Commit both `pyproject.toml` and `uv.lock`
4. CI runs with `verify-lock: 'true'` and passes

## Virtual Environment

### Automatic Activation

The action automatically activates the virtual environment created by `uv sync` at `.venv`.

**How it works**:
1. Action runs `uv sync` which creates `.venv/`
2. Action adds `.venv/bin` (or `.venv/Scripts` on Windows) to `$GITHUB_PATH`
3. Action sets `$VIRTUAL_ENV` environment variable
4. All subsequent steps use the activated environment

### Using the Environment

**Direct Python/CLI commands** (recommended):
```yaml
- uses: serapeum-org/github-actions/actions/python-setup/uv@v1
  with:
    install-groups: 'dev test'

- run: python --version
- run: pytest
- run: black .
- run: mypy src/
```

**Alternative: uv run** (also works):
```yaml
- run: uv run pytest
- run: uv run black .
```

**Manual activation** (unnecessary but possible):
```yaml
- run: |
    source .venv/bin/activate  # Linux/macOS
    python --version
```

### Environment Location

The virtual environment is always at:
- **Linux/macOS**: `$(pwd)/.venv`
- **Windows**: `$(pwd)\.venv`

**Python executable**:
- **Linux/macOS**: `.venv/bin/python`
- **Windows**: `.venv\Scripts\python.exe`

## Testing Guide

This action is comprehensively tested across multiple scenarios to ensure reliability and correct behavior. Reference the test workflow at `.github/workflows/test-python-setup-uv.yml`.

### Test Coverage Matrix

| Test Job | Purpose | Key Validations | Behavior Tested |
|----------|---------|-----------------|-----------------|
| `test-uv-basic` | Default behavior (core only) | Core dependencies installed, dev group NOT installed | `--no-default-groups` excludes optional groups by default |
| `test-uv-custom-groups` | Specific groups | Only `test` and `docs` groups installed, `dev` excluded | Group isolation with `--no-default-groups` |
| `test-uv-no-groups` | Explicit empty groups | Only core dependencies, no optional groups | Empty `install-groups: ''` handled correctly |
| `test-uv-lock-verification` | Lock validation (valid) | Lock file check passes | `uv lock --check` succeeds with up-to-date lock |
| `test-uv-lock-verification-disabled` | Skip lock check | Installation succeeds without verification | `verify-lock: 'false'` skips validation |
| `test-uv-lock-verification-fail` | Outdated lock handling | Action fails gracefully with clear error | Outdated lock detected and reported |
| `test-uv-matrix` | Cross-platform/version | Python 3.10/3.11/3.12 on Linux/Windows/macOS | Platform-specific virtual environment activation |
| `test-uv-cache` | Dependency caching | Cache populated and restored based on `uv.lock` hash | `enable-cache: true` with `cache-dependency-glob` |
| `test-uv-comma-separated-groups` | Group parsing | `'dev,test,docs'` format parsed correctly | Multiple separator handling |
| `test-uv-mixed-separators` | Group parsing | `'dev, test docs'` format parsed correctly | Flexible formatting support |
| `test-uv-space-separated-groups` | Group parsing | `'dev test docs'` format parsed correctly | Space-separated groups |
| `test-uv-no-dependency-groups-section` | Missing groups section | Works without `[dependency-groups]` in pyproject.toml | Graceful handling of missing section |
| `test-uv-explicit-dev-group` | Specific dev group | Only dev group installed when requested | Explicit group selection |
| `test-uv-groups-and-extras` | Mixed groups/extras | Both groups and extras install correctly | `--group` and `--extra` flags together |
| `test-uv-extras-only` | Extras without groups | Only extras installed, groups excluded | `extras:` prefix handling |
| `test-uv-reverse-order` | Order independence | Same result regardless of groups/extras order | Parser handles any order |

### Test Scenarios Details

**Default Behavior Test (`test-uv-basic`):**
- **Validates**: Core dependencies installed, optional groups excluded by default
- **Key assertion**: `httpx` from dev group should NOT be present
- **Purpose**: Verify `--no-default-groups` prevents automatic group installation

**Custom Groups Test (`test-uv-custom-groups`):**
- **Validates**: Only requested groups (`test`, `docs`) installed
- **Key assertion**: `httpx` from dev group should NOT be present
- **Purpose**: Verify group isolation and `--no-default-groups` behavior

**Lock Verification Test (`test-uv-lock-verification`):**
- **Validates**: `uv lock --check` passes with synchronized lock file
- **Purpose**: Ensure lock file validation works correctly

**Lock Verification Failure Test (`test-uv-lock-verification-fail`):**
- **Setup**: Modifies `pyproject.toml` after generating lock file
- **Validates**: Action fails with clear error message
- **Purpose**: Verify outdated lock detection

**Matrix Test (`test-uv-matrix`):**
- **Validates**: Works across Python 3.10, 3.11, 3.12 on ubuntu, windows, macos
- **Purpose**: Cross-platform and cross-version compatibility

**Format Tests (`comma-separated`, `mixed-separators`, `space-separated`):**
- **Validates**: All group specification formats produce identical results
- **Purpose**: Flexible input format support

### Test Fixtures

Tests use inline pyproject.toml creation for maximum clarity:

**Basic Test Example:**
```yaml
- name: Create test project with uv
  run: |
    cat > pyproject.toml << 'EOF'
    [project]
    name = "test-uv-basic"
    version = "0.1.0"
    requires-python = ">=3.12"
    dependencies = ["requests"]

    [dependency-groups]
    dev = ["httpx"]
    EOF

    pip install uv
    uv lock
```

**Custom Groups Test Example:**
```yaml
- name: Create test project with multiple groups
  run: |
    cat > pyproject.toml << 'EOF'
    [project]
    name = "test-uv-groups"
    version = "0.1.0"
    requires-python = ">=3.12"
    dependencies = ["requests"]

    [dependency-groups]
    dev = ["httpx"]
    test = ["pytest-cov", "pytest-mock"]
    docs = ["mkdocs"]
    EOF

    pip install uv
    uv lock
```

### Running Tests Locally

**Using act (GitHub Actions locally):**
```bash
# Install act
choco install act-cli  # Windows
brew install act       # macOS
winget install nektos.act  # Windows (alternative)

# Run specific test
act -j test-uv-basic
act -j test-uv-custom-groups
act -j test-uv-matrix

# Run all uv tests
act -j test-uv-*
```

**Manual testing in your repository:**
```yaml
# .github/workflows/test-uv-action.yml
name: Test uv action

on: [push, pull_request]

jobs:
  test-basic:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: serapeum-org/github-actions/actions/python-setup/uv@v1
        with:
          install-groups: 'groups: dev test'
      - run: pytest

  test-groups-isolation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: serapeum-org/github-actions/actions/python-setup/uv@v1
        with:
          install-groups: 'groups: test'
      
      - name: Verify only test group
        run: |
          python -c "import pytest; print('[OK] Test group installed')"
          # Verify dev group NOT installed
          python -c "import black" 2>&1 && exit 1 || echo "[OK] Dev group not installed"

  test-lock-verification:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: serapeum-org/github-actions/actions/python-setup/uv@v1
        with:
          verify-lock: 'true'
      - run: echo "Lock file verified"
```

### Expected Test Behaviors

**Group Isolation:**
- When `install-groups: 'groups: test'` specified, ONLY test group installed
- Dev, docs, and other groups explicitly excluded via `--no-default-groups`
- Core dependencies always installed

**Lock File Verification:**
- With `verify-lock: 'true'`: Fails if lock outdated
- With `verify-lock: 'false'`: Uses lock as-is without checking
- Default is `'true'` for safety

**Virtual Environment Activation:**
- `.venv/bin` (Linux/macOS) or `.venv/Scripts` (Windows) added to PATH
- `VIRTUAL_ENV` environment variable set
- Subsequent steps can use `python` and CLI tools directly

**Cache Behavior:**
- First run: Downloads and caches dependencies
- Subsequent runs: Restores from cache based on `uv.lock` hash
- Cache invalidates automatically when lock file changes

### Debugging Failed Tests

**Verify Python and uv installation:**
```yaml
- name: Debug environment
  run: |
    python --version
    uv --version
    which python
    which uv
```

**Check installed packages:**
```yaml
- name: List packages
  run: |
    uv pip list
    python -c "import sys; print(sys.path)"
```

**Test specific imports:**
```yaml
- name: Test imports
  run: |
    python -c "import pytest; print('pytest OK')"
    python -c "import black; print('black OK')" || echo "black not installed (expected?)"
```

**Verify virtual environment:**
```yaml
- name: Check venv
  run: |
    echo "VIRTUAL_ENV: $VIRTUAL_ENV"
    echo "PATH: $PATH"
    ls -la .venv/
```

**Check lock file:**
```yaml
- name: Verify lock
  run: |
    cat pyproject.toml
    ls -la uv.lock
    uv lock --check
```

### Test Assertions Examples

**Positive assertion (should be installed):**
```bash
python -c "import pytest; print('[OK] pytest installed')"
```

**Negative assertion (should NOT be installed):**
```bash
if python -c "import httpx" 2>/dev/null; then
  echo "[ERROR] httpx should not be installed"
  exit 1
else
  echo "[OK] httpx not installed as expected"
fi
```

**Version assertion:**
```bash
python -c "import sys; assert sys.version_info[:2] == (3, 12), 'Wrong Python version'"
```

### Continuous Integration Best Practices

**Matrix testing:**
```yaml
strategy:
  matrix:
    python-version: ['3.10', '3.11', '3.12']
    os: [ubuntu-latest, windows-latest, macos-latest]
    groups: ['dev', 'test', 'dev test', '']

steps:
  - uses: .../actions/python-setup/uv@v1
    with:
      python-version: ${{ matrix.python-version }}
      install-groups: ${{ matrix.groups && format('groups: {0}', matrix.groups) || '' }}
```

**Fail-fast disabled for comprehensive testing:**
```yaml
strategy:
  fail-fast: false  # Test all combinations even if one fails
  matrix:
    # ... matrix configuration
```

## Troubleshooting

### Error: "The lockfile at `uv.lock` needs to be updated"

**Cause**: Lock file is outdated compared to `pyproject.toml`.

**Solution**:
```bash
# Update lock file locally
uv lock

# Commit the changes
git add pyproject.toml uv.lock
git commit -m "Update dependencies"
git push
```

**Or** disable verification temporarily:
```yaml
- uses: serapeum-org/github-actions/actions/python-setup/uv@v1
  with:
    verify-lock: 'false'
```

### Error: "No such file or directory: uv.lock"

**Cause**: Lock file doesn't exist in repository.

**Solution**:
```bash
# Generate lock file
uv lock

# Commit it
git add uv.lock
git commit -m "Add uv.lock file"
git push
```

### Wrong Python Version

**Issue**: Action installs Python 3.12 but need 3.10.

**Solution**: Specify version explicitly:
```yaml
- uses: serapeum-org/github-actions/actions/python-setup/uv@v1
  with:
    python-version: '3.10'
```

### Dependency Not Found After Installation

**Issue**: `ModuleNotFoundError` even after installation.

**Possible causes**:
1. **Group not specified**: Dependency is in optional group not requested
   ```yaml
   # Wrong: dev group has pytest but not installed
   install-groups: 'test'

   # Fix: Add dev group
   install-groups: 'dev test'
   ```

2. **Wrong import name**: Package name ≠ import name
   ```toml
   # Package: "pyyaml", Import: "yaml"
   dependencies = ["pyyaml"]
   ```
   ```python
   import yaml  # Not: import pyyaml
   ```

### Groups Not Isolated

**Issue**: Unwanted packages installed even though group not specified.

**Cause**: Before the fix, the action used `--group` which included default groups.

**Solution**: Use latest version of the action which uses `--no-default-groups`:
```yaml
- uses: serapeum-org/github-actions/actions/python-setup/uv@v1  # Latest
```

### Virtual Environment Not Activated

**Issue**: `python: command not found` or wrong Python version.

**Verification**:
```yaml
- run: |
    echo "Python: $(which python)"
    echo "PATH: $PATH"
    echo "VIRTUAL_ENV: $VIRTUAL_ENV"
```

**Expected output**:
```
Python: /home/runner/work/repo/repo/.venv/bin/python
PATH: /home/runner/work/repo/repo/.venv/bin:...
VIRTUAL_ENV: /home/runner/work/repo/repo/.venv
```

**If not working**: Check GitHub Actions runner logs for warnings in "Activate virtual environment" step.

### Cache Not Working

**Symptoms**: Dependencies reinstall on every run.

**Debug**:
1. Check `uv.lock` exists and is committed
2. Verify cache hit in action logs:
   ```
   Restored cache from key: setup-uv-...
   ```
3. Check lock file hasn't changed between runs

**Force cache refresh**:
Change `uv.lock` content (update dependencies).

## Best Practices

### 1. Always Commit Lock File

```bash
# Generate lock file
uv lock

# Always commit both files together
git add pyproject.toml uv.lock
git commit -m "Update dependencies"
```

**Why**: Ensures reproducible builds across all environments.

### 2. Use Specific Python Versions

```yaml
# Good: Explicit version
python-version: '3.11'

# Avoid: Version ranges or latest
python-version: '3.x'  # Too broad
```

### 3. Organize Dependency Groups by Purpose

```toml
# Good: Clear separation
[dependency-groups]
dev = ["black", "mypy", "ruff"]
test = ["pytest", "pytest-cov"]
docs = ["mkdocs"]

# Avoid: Single "dev" group for everything
[dependency-groups]
dev = ["black", "mypy", "pytest", "mkdocs"]  # Too broad
```

### 4. Use Lock Verification in CI

```yaml
# Good: Catch dependency drift early
- uses: serapeum-org/github-actions/actions/python-setup/uv@v1
  with:
    verify-lock: 'true'  # Default, but explicit is clear
```

### 5. Pin Action Versions

```yaml
# Good: Pin to major version (gets updates)
- uses: serapeum-org/github-actions/actions/python-setup/uv@v1

# Good: Pin to exact commit (maximum stability)
- uses: serapeum-org/github-actions/actions/python-setup/uv@abc1234

# Avoid: Using @main (unpredictable)
- uses: serapeum-org/github-actions/actions/python-setup/uv@main
```

### 6. Separate Workflows by Purpose

```yaml
# lint.yml
- uses: .../actions/python-setup/uv@v1
  with:
    install-groups: 'dev'
- run: black --check .
- run: mypy src/

# test.yml
- uses: .../actions/python-setup/uv@v1
  with:
    install-groups: 'test'
- run: pytest

# docs.yml
- uses: .../actions/python-setup/uv@v1
  with:
    install-groups: 'docs'
- run: mkdocs build
```

### 7. Use Matrix for Multi-Version Testing

```yaml
strategy:
  matrix:
    python-version: ['3.10', '3.11', '3.12']
    os: [ubuntu-latest, windows-latest, macos-latest]

steps:
  - uses: .../actions/python-setup/uv@v1
    with:
      python-version: ${{ matrix.python-version }}
```

## Comparison with Other Actions

| Feature | This Action | actions/setup-python | astral-sh/setup-uv alone |
|---------|-------------|----------------------|--------------------------|
| Python Installation | ✓ | ✓ | ✗ (requires setup-python) |
| uv Installation | ✓ | ✗ | ✓ |
| Dependency Installation | ✓ (automatic) | ✗ (manual) | ✗ (manual) |
| Group Support | ✓ (built-in) | ✗ | ✓ (manual) |
| Lock Verification | ✓ (built-in) | ✗ | ✗ (manual) |
| Auto VEnv Activation | ✓ | ✗ | ✗ |
| Dependency Caching | ✓ | ✓ (pip only) | ✓ |
| Group Isolation | ✓ (`--no-default-groups`) | N/A | ✗ (manual) |

**When to use this action:**
- Modern Python projects using `pyproject.toml`
- Need dependency group support
- Want automatic environment activation
- Prefer uv's speed over pip

**When to use alternatives:**
- `actions/setup-python` alone: Minimal setup, no uv needed
- `astral-sh/setup-uv` alone: Need full control over uv commands

## Additional Resources

- [uv documentation](https://docs.astral.sh/uv/)
- [PEP 735: Dependency Groups](https://peps.python.org/pep-0735/)
- [actions/setup-python](https://github.com/actions/setup-python)
- [astral-sh/setup-uv](https://github.com/astral-sh/setup-uv)

## Support

For issues, questions, or contributions:
- Repository: https://github.com/serapeum-org/github-actions
- Issues: https://github.com/serapeum-org/github-actions/issues
