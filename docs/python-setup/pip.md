# Python Setup with pip - Complete Guide

Composite GitHub Action for setting up Python environments with pip package manager, designed for projects using `pyproject.toml` for dependency management.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Inputs Reference](#inputs-reference)
- [Features](#features)
- [Usage Scenarios](#usage-scenarios)
- [Cache Configuration](#cache-configuration)
- [Dependency Groups](#dependency-groups)
- [Testing Guide](#testing-guide)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Overview

This action wraps `actions/setup-python@v6` with additional functionality for managing pip-based Python projects. It provides:

- Automatic Python installation and configuration
- Optional dependency caching for faster CI runs
- Support for `pyproject.toml` optional dependency groups
- Automatic pip upgrade
- Cross-platform support (Linux, Windows, macOS)
- Architecture selection (x64, x86)

**Location**: `serapeum-org/github-actions/actions/python-setup/pip@v1`

## Quick Start

### Basic Usage (No Cache)

```yaml
steps:
  - uses: actions/checkout@v5
  - uses: serapeum-org/github-actions/actions/python-setup/pip@v1
```

This sets up Python 3.12 (default) without caching. Suitable for projects without `pyproject.toml` or `requirements.txt`.

### With Caching

```yaml
steps:
  - uses: actions/checkout@v5
  - uses: serapeum-org/github-actions/actions/python-setup/pip@v1
    with:
      cache: 'pip'
```

**Important**: Caching requires either `pyproject.toml` or `requirements.txt` in your repository root.

### With Optional Dependencies (Extras)

```yaml
steps:
  - uses: actions/checkout@v5
  - uses: serapeum-org/github-actions/actions/python-setup/pip@v1
    with:
      install-groups: 'extras: dev test'
```

Installs your package with `pip install .[dev,test]`.

## Inputs Reference

| Input | Description | Required | Default | Valid Values |
|-------|-------------|----------|---------|--------------|
| `python-version` | Python version to install | No | `'3.12'` | Any valid Python version (e.g., `'3.10'`, `'3.11'`, `'3.12'`) |
| `cache` | Enable dependency caching | No | `''` (disabled) | `''`, `'pip'`, `'pipenv'`, `'poetry'` |
| `architecture` | Target CPU architecture | No | `'x64'` | `'x64'`, `'x86'` |
| `install-groups` | Dependency groups and/or optional dependencies to install | No | `''` (none) | Format: `'groups: name1 name2, extras: extra1 extra2'` |

### Input Details

#### `python-version`
Specifies which Python version to install. Supports:
- Major.minor versions: `'3.11'`, `'3.12'`, `'3.13'`
- Full versions: `'3.11.5'`
- Version ranges: `'3.x'`, `'>=3.11'`

#### `cache`
Controls dependency caching via `actions/setup-python@v6`:
- `''` (empty string, default): No caching. Use when no `pyproject.toml` or `requirements.txt` exists.
- `'pip'`: Cache pip dependencies from `pyproject.toml` or `requirements.txt`
- `'pipenv'`: Cache pipenv dependencies from `Pipfile.lock`
- `'poetry'`: Cache poetry dependencies from `poetry.lock`

**Cache Validation**: If `cache` is non-empty, the action validates that `pyproject.toml` or `requirements.txt` exists. If neither file is found, the action fails with a clear error message.

#### `architecture`
Selects CPU architecture (mainly relevant for Windows):
- `'x64'`: 64-bit Python (default, recommended)
- `'x86'`: 32-bit Python (legacy systems)

#### `install-groups`
Specifies dependency groups from `[dependency-groups]` and/or optional dependencies from `[project.optional-dependencies]` in `pyproject.toml`.

**Format**: `'groups: group1 group2, extras: extra1 extra2'`

**Examples**:
- Only dependency groups: `'groups: dev test'`
- Only optional dependencies: `'extras: aws viz'`
- Mixed: `'groups: dev test, extras: aws viz'`
- Legacy format (still works): `'dev test'` (interpreted as extras for backward compatibility)

**Behavior**:
- Optional dependencies (extras) use `pip install .[extra1,extra2]`
- Dependency groups use `pip install . --group group1 --group group2` (requires pip >= 25.1 for PEP 735 support)
- If pip doesn't support `--group`, the action fails with an error instead of silently skipping the requested groups

If `install-groups` is empty and `pyproject.toml` exists, runs `pip install .` (installs only core dependencies).

**Breaking change (`pip/v1`)**: Requesting dependency groups (`groups: ...`) on pip older than 25.1 now fails the
job (`exit 1`) instead of emitting a warning and installing only core + extras. Upgrade the runner's pip to
>= 25.1, or use the `uv` action, which has native PEP 735 support.

## Features

### 1. Cache Validation

The action validates cache requirements **before** running `actions/setup-python@v6`:

```yaml
# This will FAIL with a clear error
- uses: ./actions/python-setup/pip
  with:
    cache: 'pip'  # No pyproject.toml or requirements.txt exists

# Error message:
# Cache is enabled (cache='pip') but no pyproject.toml or requirements.txt found.
# Either create a pyproject.toml/requirements.txt file or set cache: '' to disable caching.
```

### 2. Smart Dependency Installation

The action intelligently handles different scenarios:

| Scenario | `pyproject.toml` exists? | `install-groups` | Command Executed |
|----------|--------------------------|------------------|------------------|
| No file | No | Any | Skipped (message logged) |
| Basic install | Yes | Empty | `pip install .` |
| With groups | Yes | `'dev test'` | `pip install .[dev,test]` |

### 3. Automatic Pip Upgrade

Always runs `python -m pip install --upgrade pip` after Python setup to ensure the latest pip version.

### 4. Package Summary

Lists installed packages after installation for debugging:
```
pip list
```

### 5. Grouped Output

All actions are grouped in GitHub Actions logs for better readability:
- "Validating cache requirements"
- "Upgrading pip"
- "Installing dependencies"
- "Installed packages summary"

## Usage Scenarios

### Scenario 1: Basic Install (No Dependency Files)

**Use Case**: Testing the action itself, simple scripts without dependencies, or when you'll install dependencies manually.

**Workflow:**
```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: serapeum-org/github-actions/actions/python-setup/pip@v1

      - name: Verify Python installation
        run: |
          python --version
          pip --version
```

**What Happens**:
- Python 3.12 installed (default)
- Pip upgraded to latest
- No dependencies installed (logs "No pyproject.toml found - skipping package installation")
- Cache disabled by default

**When to use**: Quick scripts, action testing, or when you prefer manual `pip install` commands

### Scenario 2: Basic Project with pyproject.toml

**Use Case**: Standard Python package with core dependencies.

```yaml
# pyproject.toml
[project]
name = "my-package"
version = "1.0.0"
dependencies = ["requests", "numpy"]
```

```yaml
- uses: actions/checkout@v5
- uses: serapeum-org/github-actions/actions/python-setup/pip@v1
  with:
    cache: 'pip'
```

**What Happens**:
- Python installed with caching
- Pip upgraded
- `pip install .` executed (installs requests, numpy, and your package)

### Scenario 3: Development with Optional Dependencies

**Use Case**: Running tests and linters that require dev dependencies.

```yaml
# pyproject.toml
[project]
name = "my-package"
dependencies = ["requests"]

[project.optional-dependencies]
dev = ["pytest", "black", "mypy"]
test = ["pytest-cov", "pytest-mock"]
docs = ["mkdocs", "mkdocs-material"]

[dependency-groups]
lint = ["ruff", "flake8"]
build = ["build", "twine"]
```

```yaml
- uses: actions/checkout@v5
- uses: serapeum-org/github-actions/actions/python-setup/pip@v1
  with:
    cache: 'pip'
    install-groups: 'extras: dev test'
```

**What Happens**:
- Python installed with caching
- `pip install .[dev,test]` executed
- Installs: requests (core), pytest, black, mypy (dev), pytest-cov, pytest-mock (test)

### Scenario 4: Matrix Testing Across Python Versions

**Use Case**: Testing compatibility with multiple Python versions.

```yaml
strategy:
  matrix:
    python-version: ['3.10', '3.11', '3.12']
    os: [ubuntu-latest, windows-latest, macos-latest]

steps:
  - uses: actions/checkout@v5
  - uses: serapeum-org/github-actions/actions/python-setup/pip@v1
    with:
      python-version: ${{ matrix.python-version }}
      cache: 'pip'
```

**What Happens**:
- Tests run on 9 combinations (3 Python versions × 3 OS platforms)
- Each uses cached dependencies for faster runs

### Scenario 5: Using requirements.txt Instead

**Use Case**: Legacy project using `requirements.txt`.

```yaml
# requirements.txt
requests==2.31.0
numpy==1.26.0
```

```yaml
- uses: actions/checkout@v5
- uses: serapeum-org/github-actions/actions/python-setup/pip@v1
  with:
    cache: 'pip'
```

**What Happens**:
- Python installed with caching (validates `requirements.txt` exists)
- Pip upgraded
- No automatic installation (you must run `pip install -r requirements.txt` separately)

### Scenario 6: Windows 32-bit Architecture

**Use Case**: Supporting legacy Windows systems.

```yaml
- uses: actions/checkout@v5
- uses: serapeum-org/github-actions/actions/python-setup/pip@v1
  with:
    architecture: 'x86'
    cache: 'pip'
```

### Scenario 7: Mixed Groups and Extras

**Use Case**: Installing both dependency groups (PEP 735) and optional dependencies (extras) together.

**`pyproject.toml`:**
```toml
[project]
name = "my-package"
dependencies = ["requests"]

[project.optional-dependencies]
aws = ["boto3", "s3fs"]

[dependency-groups]
dev = ["httpx", "pytest"]
```

**Workflow:**
```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: serapeum-org/github-actions/actions/python-setup/pip@v1
        with:
          cache: 'pip'
          install-groups: 'groups: dev, extras: aws'

      - name: Verify installation
        shell: bash
        run: |
          python -c "import requests; print('[OK] Core dependencies installed')"
          python -c "import boto3; print('[OK] AWS extra installed')"
          # Requested dev group is guaranteed installed (the action fails otherwise)
          python -c "import httpx; print('[OK] Dev group installed')"
```

**What Happens**:
- Core dependencies: `requests` (always installed)
- Optional dependencies (extras): `boto3`, `s3fs` (always works with pip)
- Dependency groups: `httpx`, `pytest` (requires pip >= 25.1 for PEP 735 support)
- Fails with an error if pip doesn't support `--group`

### Scenario 8: Poetry/Pipenv Projects

**Use Case**: Using alternative package managers with their specific lock files.

**With Poetry:**
```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: serapeum-org/github-actions/actions/python-setup/pip@v1
        with:
          cache: 'poetry'

      - name: Install with Poetry
        run: |
          pip install poetry
          poetry install
```

**With Pipenv:**
```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: serapeum-org/github-actions/actions/python-setup/pip@v1
        with:
          cache: 'pipenv'

      - name: Install with Pipenv
        run: |
          pip install pipenv
          pipenv install
```

### Scenario 9: Empty Groups/Extras Handling

**Use Case**: Testing edge cases with empty values in install-groups.

**Workflow:**
```yaml
jobs:
  test-empty-groups:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: serapeum-org/github-actions/actions/python-setup/pip@v1
        with:
          install-groups: 'groups: , extras: aws'

      - name: Verify handling
        shell: bash
        run: |
          pip list
          python -c "import requests; print('[OK] Core dependencies')"
          python -c "import boto3; print('[OK] AWS extra despite empty groups')"
```

**What Happens**:
- Empty groups section is gracefully ignored
- Core dependencies still installed
- AWS extra installs normally

### Scenario 10: Invalid Format Handling

**Use Case**: Understanding how the action handles malformed input.

**Workflow:**
```yaml
jobs:
  test-invalid:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: serapeum-org/github-actions/actions/python-setup/pip@v1
        with:
          install-groups: 'invalid format without colons'

      - name: Verify warning shown
        shell: bash
        run: |
          # Action will show warning but still install core dependencies
          python -c "import requests; print('[OK] Core dependencies installed despite invalid format')"
```

**What Happens**:
- Warning logged: "No 'groups:' or 'extras:' sections found"
- Core dependencies still installed
- Workflow continues (doesn't fail)

### Scenario 11: Whitespace Handling

**Use Case**: Flexible formatting with extra whitespace in install-groups.

**Workflow:**
```yaml
jobs:
  test-whitespace:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: serapeum-org/github-actions/actions/python-setup/pip@v1
        with:
          install-groups: '  groups:  dev   test  ,  extras:  aws   viz  '

      - name: Verify whitespace handling
        shell: bash
        run: |
          python -c "import boto3; print('[OK] AWS extra installed')"
          python -c "import matplotlib; print('[OK] Viz extra installed')"
```

**What Happens**:
- Leading/trailing whitespace trimmed
- Multiple spaces between groups handled correctly
- Groups parsed: `dev`, `test`, `aws`, `viz`

### Scenario 12: Only Core Dependencies

**Use Case**: Installing just the package without any optional groups or extras.

**`pyproject.toml`:**
```toml
[project]
name = "my-package"
dependencies = ["requests", "click", "httpx"]

[project.optional-dependencies]
dev = ["pytest", "black"]

[dependency-groups]
test = ["pytest-cov"]
```

**Workflow:**
```yaml
jobs:
  production-install:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: serapeum-org/github-actions/actions/python-setup/pip@v1
        # No install-groups parameter

      - name: Verify only core installed
        shell: bash
        run: |
          pip list
          python -c "import requests, click, httpx; print('[OK] Core dependencies')"
          echo "[OK] Only core dependencies installed as expected"
```

**What Happens**:
- Runs `pip install .` without any extras or groups
- Only `dependencies` from `[project]` section installed
- Optional dependencies and groups not installed

### Scenario 13: All Combinations (Comprehensive Test)

**Use Case**: Installing multiple groups and extras simultaneously.

**`pyproject.toml`:**
```toml
[project]
name = "enterprise-app"
dependencies = ["requests", "click"]

[project.optional-dependencies]
aws = ["boto3", "s3fs"]
azure = ["azure-storage-blob"]
gcp = ["google-cloud-storage"]

[dependency-groups]
dev = ["httpx", "black", "mypy"]
test = ["pytest", "pytest-cov"]
docs = ["mkdocs", "mkdocstrings"]
```

**Workflow:**
```yaml
jobs:
  comprehensive-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: serapeum-org/github-actions/actions/python-setup/pip@v1
        with:
          cache: 'pip'
          install-groups: 'groups: dev test docs, extras: aws azure gcp'

      - name: Verify comprehensive installation
        shell: bash
        run: |
          # Verify core
          python -c "import requests, click; print('[OK] Core dependencies')"
          # Verify all extras
          python -c "import boto3; print('[OK] AWS extra')"
          python -c "from azure.storage.blob import BlobServiceClient; print('[OK] Azure extra')"
          python -c "from google.cloud import storage; print('[OK] GCP extra')"
          # Verify groups (if pip supports)
          if python -c "import httpx, pytest, mkdocs" 2>/dev/null; then
            echo "[OK] All dependency groups installed"
          else
            echo "[OK] Dependency groups not installed (pip doesn't support PEP 735)"
          fi
```

**What Happens**:
- Core: `requests`, `click`
- Extras: All cloud provider SDKs
- Groups: Dev, test, docs tools (if pip supports PEP 735)

### Scenario 14: Reverse Order (Extras Before Groups)

**Use Case**: Verifying order doesn't matter.

**Workflow:**
```yaml
jobs:
  test-order:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: serapeum-org/github-actions/actions/python-setup/pip@v1
        with:
          install-groups: 'extras: aws, groups: dev'

      - name: Verify order handling
        shell: bash
        run: |
          python -c "import boto3; print('[OK] AWS extra installed')"
          if python -c "import httpx" 2>/dev/null; then
            echo "[OK] Dev group installed"
          fi
```

**What Happens**:
- Action parses both sections regardless of order
- Same result as `'groups: dev, extras: aws'`

## Cache Configuration

### When to Enable Cache

**Enable cache (`cache: 'pip'`) when:**
- You have `pyproject.toml` or `requirements.txt`
- Your dependencies don't change frequently
- You want faster CI runs (caching can save 30-60 seconds per run)

**Disable cache (`cache: ''`) when:**
- No `pyproject.toml` or `requirements.txt` exists
- Dependencies change on every commit
- Testing the action itself
- Debugging dependency issues

### Cache Validation Flow

```
User sets cache: 'pip'
    ↓
Action checks for pyproject.toml or requirements.txt
    ↓
Found? → Yes → Continue to setup-python (cache enabled)
       → No  → FAIL with error message
```

### Cache Example: Before and After

**Without Cache** (60-90 seconds):
```
Set up Python: 10s
Install dependencies: 50-80s
Total: 60-90s
```

**With Cache** (20-30 seconds):
```
Set up Python: 10s
Restore cache: 5s
Install dependencies: 5-15s (only new/changed packages)
Total: 20-30s
```

## Dependency Groups

### Optional Dependencies vs Dependency Groups

**Key Differences**:

1. **Optional Dependencies** (`[project.optional-dependencies]`):
   - Part of PEP 621 standard, **widely supported** by all pip versions
   - Published with your package on PyPI
   - Installed using `pip install package[extra]` syntax
   - Use prefix `extras:` in this action
   - **Always works reliably**

2. **Dependency Groups** (`[dependency-groups]`):
   - Part of PEP 735 standard (**newer, limited support**)
   - Development-only, **not published** with package
   - Installed using `pip install . --group <name>` (requires pip >= 25.1)
   - Use prefix `groups:` in this action
   - **The action fails** if pip version doesn't support PEP 735 (`--group`)

**Recommendation**: Use optional dependencies (extras) for maximum compatibility. Use dependency groups only if you need PEP 735 features.

**Note**: If your pip version doesn't support the `--group` flag (pip < 25.1), the action fails with an error pointing you at pip >= 25.1 or the uv action, which has full PEP 735 support. It will not silently skip the requested groups.

### Understanding Optional Dependencies (Extras)

`pyproject.toml` supports optional dependency groups using extras:

```toml
[project]
name = "myapp"
dependencies = ["requests"]  # Core dependencies (always installed)

[project.optional-dependencies]
dev = ["pytest", "black"]      # Development tools
test = ["pytest-cov"]          # Testing tools
docs = ["mkdocs"]              # Documentation tools
aws = ["boto3", "s3fs"]        # AWS integration
viz = ["matplotlib", "seaborn"]  # Visualization
all = ["pytest", "black", "pytest-cov", "mkdocs", "boto3", "s3fs", "matplotlib", "seaborn"]  # Everything
```

### Understanding Dependency Groups (PEP 735)

Dependency groups are an alternative for development-only dependencies:

```toml
[project]
name = "myapp"
dependencies = ["requests"]

[dependency-groups]
dev = ["httpx>=0.25", "rich>=13.0"]
test = ["pytest>=7.0", "pytest-cov>=4.0"]
docs = ["mkdocs>=1.5", "mkdocstrings>=0.24"]
```

### Installing Groups and Extras

| `install-groups` Value | Commands Generated | What Gets Installed |
|------------------------|-------------------|---------------------|
| `''` (empty) | `pip install .` | Core dependencies only |
| `'extras: dev'` | `pip install .[dev]` | Core + dev extras |
| `'extras: dev test'` | `pip install .[dev,test]` | Core + dev + test extras |
| `'groups: lint'` | `pip install .` then `pip install . --group lint` | Core + lint group |
| `'groups: lint build, extras: dev'` | `pip install .[dev]` then `pip install . --group lint --group build` | Core + dev extras + lint/build groups |
| `'extras: aws viz, groups: dev'` | `pip install .[aws,viz]` then `pip install . --group dev` | Core + AWS/viz extras + dev group |

### PEP 735 Support and Errors

**When pip supports `--group` (pip >= 25.1):**
```
=== Installation Summary ===
✓ Dependency groups will be installed: dev test
✓ Optional dependencies (extras) will be installed: aws
✓ Core dependencies will always be installed
==========================

Installing package with optional dependencies: pip install .[aws]
Installing dependency groups: pip install . --group dev --group test
```

**When pip doesn't support `--group` (pip < 25.1):**
```
Error: pip 24.0 does not support the --group flag (PEP 735 dependency groups).
Error: Dependency groups were explicitly requested (dev,test) but cannot be installed, so this step is failing instead of silently skipping them.
Error: Upgrade to pip >= 25.1 (which ships the --group option), or use the uv action which has native PEP 735 support.
```

Because the requested groups cannot be honored, the action **fails the job** rather than silently skipping them. Core dependencies and extras are installed before this check, but the step exits non-zero so the missing groups cannot go unnoticed.

### Common Patterns

**Test Workflow (using extras for compatibility)**:
```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: serapeum-org/github-actions/actions/python-setup/pip@v1
        with:
          install-groups: 'extras: test'
      - run: pytest --cov=src
```

**Lint Workflow (using extras)**:
```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: serapeum-org/github-actions/actions/python-setup/pip@v1
        with:
          install-groups: 'extras: dev'
      - run: black --check .
      - run: mypy src/
```

**Documentation Workflow**:
```yaml
jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: serapeum-org/github-actions/actions/python-setup/pip@v1
        with:
          install-groups: 'extras: docs'
      - run: mkdocs build
      - run: mkdocs gh-deploy --force
```

**Combined Workflow (extras + groups)**:
```yaml
jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: serapeum-org/github-actions/actions/python-setup/pip@v1
        with:
          install-groups: 'groups: dev test, extras: aws'
      - run: black --check .
      - run: pytest
```

**Production Installation (core only)**:
```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: serapeum-org/github-actions/actions/python-setup/pip@v1
        # No install-groups = core only
      - run: python app.py
```

### Migrating from Dependency Groups to Extras

If your pip is older than 25.1 and the action fails on unsupported `--group`, consider:

**Option 1: Use optional dependencies (extras) instead**
```toml
# Before (dependency groups - limited support)
[dependency-groups]
dev = ["pytest", "black"]

# After (optional dependencies - universal support)
[project.optional-dependencies]
dev = ["pytest", "black"]
```

**Option 2: Use the uv action** (has full PEP 735 support)
```yaml
# Instead of pip action
- uses: serapeum-org/github-actions/actions/python-setup/uv@v1
  with:
    install-groups: 'groups: dev test'  # Full PEP 735 support
```

## Testing Guide

This action is comprehensively tested across multiple scenarios to ensure reliability. Reference the test workflow at `.github/workflows/test-python-setup-pip.yml`.

### Test Coverage Matrix

| Test Job | Purpose | Key Validations | Fixture |
|----------|---------|-----------------|---------|
| `test-pip-basic` | Default behavior without cache | Python installed, no cache validation | - |
| `test-pip-with-groups` | Optional dependencies (extras) | Multiple extras installed correctly | `test-pip-with-groups/` |
| `test-pip-matrix` | Cross-platform compatibility | Works on Linux/Windows/macOS with Python 3.11/3.12/3.13/3.14 | `test-pip-matrix/` |
| `test-pip-cache` | Cache functionality | Dependencies cached and restored | `test-pip-cache/` |
| `test-pip-architecture` | Architecture selection | x64 and x86 work correctly on Windows | `test-pip-architecture/` |
| `test-pip-cache-validation-error` | Cache validation error handling | Fails gracefully when cache enabled without files | - |
| `test-pip-cache-with-requirements` | requirements.txt support | Cache validation passes with requirements.txt | `test-pip-cache-with-requirements/` |
| `test-pip-no-dependency-file` | No dependency files | Works without pyproject.toml/requirements.txt when cache disabled | - |
| `test-pip-empty-sections` | Empty groups/extras sections | Empty groups handled gracefully | `test-pip-empty-sections/` |
| `test-pip-invalid-format` | Invalid format handling | Shows warning, continues with core deps | `test-pip-invalid-format/` |
| `test-pip-optional-dependencies` | Optional dependencies (extras) | Extras installed, groups show warning | `test-pip-optional-dependencies/` |
| `test-pip-mixed-groups-and-extras` | Mixed groups and extras | Both types install (groups if supported) | `test-pip-mixed-groups-and-extras/` |
| `test-pip-dependency-groups-only` | Dependency groups only | Groups install if pip supports PEP 735 | `test-pip-dependency-groups-only/` |
| `test-pip-groups-docs-only` | Single dependency group (docs) | Shows expected warning for unsupported pip | `test-pip-groups-only-docs/` |
| `test-pip-all-combinations` | All combinations (groups + extras) | Comprehensive installation of multiple groups/extras | `test-pip-all-combinations/` |
| `test-pip-single-extra` | Single extra only | Single extra installs correctly | `test-pip-single-extra/` |
| `test-pip-single-group` | Single group only | Single group installs if supported | `test-pip-single-group/` |
| `test-pip-only-core-dependencies` | Core dependencies only | Only core deps, no groups/extras | `test-pip-only-dependencies/` |
| `test-pip-whitespace-handling` | Whitespace handling | Extra whitespace trimmed correctly | `test-pip-whitespace-handling/` |
| `test-pip-empty-groups-value` | Empty groups value | Empty `groups:` handled gracefully | `test-pip-empty-groups-only/` |
| `test-pip-empty-extras-value` | Empty extras value | Empty `extras:` handled gracefully | `test-pip-empty-extras-only/` |
| `test-pip-python-version-matrix` | Python version matrix | Works with multiple Python versions | `test-pip-multiple-python-versions/` |
| `test-pip-reverse-order` | Reverse order (extras before groups) | Order doesn't matter | `test-pip-all-combinations/` |
| `test-pip-cache-with-groups` | Cache with groups and extras | Caching works with install-groups | `test-pip-all-combinations/` |

### Test Fixtures Location

All test fixtures are located in `tests/data/pip/` directory:
```
tests/data/pip/
├── test-pip-with-groups/
│   └── pyproject.toml
├── test-pip-matrix/
│   └── pyproject.toml
├── test-pip-cache/
│   └── pyproject.toml
├── test-pip-architecture/
│   └── pyproject.toml
├── test-pip-cache-with-requirements/
│   └── requirements.txt
├── test-pip-empty-sections/
│   └── pyproject.toml
├── test-pip-invalid-format/
│   └── pyproject.toml
├── test-pip-optional-dependencies/
│   └── pyproject.toml
├── test-pip-mixed-groups-and-extras/
│   └── pyproject.toml
├── test-pip-dependency-groups-only/
│   └── pyproject.toml
├── test-pip-groups-only-docs/
│   └── pyproject.toml
├── test-pip-all-combinations/
│   └── pyproject.toml
├── test-pip-single-extra/
│   └── pyproject.toml
├── test-pip-single-group/
│   └── pyproject.toml
├── test-pip-only-dependencies/
│   └── pyproject.toml
├── test-pip-whitespace-handling/
│   └── pyproject.toml
├── test-pip-empty-groups-only/
│   └── pyproject.toml
├── test-pip-empty-extras-only/
│   └── pyproject.toml
└── test-pip-multiple-python-versions/
    └── pyproject.toml
```

### Example Test Fixtures

**test-pip-with-groups/pyproject.toml:**
```toml
[project]
name = "test-pip-with-groups"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = ["pytest", "black"]
test = ["pytest-cov"]
```

**test-pip-all-combinations/pyproject.toml:**
```toml
[project]
name = "test-pip-all-combinations"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["requests", "click"]

[project.optional-dependencies]
aws = ["boto3"]
azure = ["azure-storage-blob"]
gcp = ["google-cloud-storage"]

[dependency-groups]
dev = ["httpx", "black", "mypy"]
test = ["pytest", "pytest-cov"]
docs = ["mkdocs"]
```

**test-pip-cache-with-requirements/requirements.txt:**
```
requests==2.31.0
numpy>=1.26.0
```

### Running Tests Locally

Use `act` to test locally:

```bash
# Install act (if needed)
# Windows: choco install act-cli
# macOS: brew install act

# Run specific test
act -j test-pip-basic
act -j test-pip-with-groups
act -j test-pip-matrix

# Run all pip tests
act -j test-pip-*
```

### Testing in Your Own Workflow

**Basic Test:**
```yaml
# .github/workflows/test-pip-action.yml
name: Test pip action

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: serapeum-org/github-actions/actions/python-setup/pip@v1
        with:
          cache: 'pip'
          install-groups: 'extras: dev test'
      - run: pytest
```

**Matrix Test:**
```yaml
name: Matrix Test

on: [push]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.11', '3.12', '3.13']
    steps:
      - uses: actions/checkout@v5
      - uses: serapeum-org/github-actions/actions/python-setup/pip@v1
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'
          install-groups: 'extras: test'
      - run: pytest
```

**Cache Test:**
```yaml
name: Cache Test

on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      
      - name: First run (populate cache)
        uses: serapeum-org/github-actions/actions/python-setup/pip@v1
        with:
          cache: 'pip'
      
      - name: Verify cache
        run: pip list
      
      # On subsequent runs, cache will be restored automatically
```

### Expected Test Behaviors

**PEP 735 Support Detection:**
Tests verify that when dependency groups are requested (on pip >= 25.1, as used by CI runners):
- The requested groups are installed and asserted present
- Core dependencies and optional dependencies (extras) install
- If pip lacked `--group`, the action would fail the job rather than skip the groups

**Cache Validation:**
Tests verify that:
- Cache enabled without dependency files → fails with clear error
- Cache with pyproject.toml → works
- Cache with requirements.txt → works
- Cache disabled → always works

**Cross-Platform:**
Tests verify that:
- Shell commands work on Windows (PowerShell), Linux (bash), macOS (bash)
- File paths handled correctly
- Architecture selection works on Windows (x64, x86)

**Whitespace Handling:**
Tests verify that:
- Leading/trailing whitespace ignored
- Multiple spaces between groups handled
- Mixed formatting accepted

### Debugging Failed Tests

**Check action logs:**
```yaml
- name: Debug installation
  run: |
    cat pyproject.toml
    pip list
    pip show pytest
```

**Verify Python version:**
```yaml
- name: Check Python
  run: |
    python --version
    python -c "import sys; print(sys.version_info)"
```

**Test dependency imports:**
```yaml
- name: Test imports
  run: |
    python -c "import pytest; print('pytest OK')"
    python -c "import black; print('black OK')"
```

## Troubleshooting

### Error: "No file matched to [**/requirements.txt or **/pyproject.toml]"

**Cause**: `cache: 'pip'` is enabled but no `pyproject.toml` or `requirements.txt` exists.

**Solution**:
```yaml
# Option 1: Disable cache
- uses: serapeum-org/github-actions/actions/python-setup/pip@v1
  with:
    cache: ''  # Explicitly disable

# Option 2: Create pyproject.toml
- name: Create pyproject.toml
  run: |
    cat > pyproject.toml << 'EOF'
    [project]
    name = "myproject"
    version = "0.1.0"
    EOF

- uses: serapeum-org/github-actions/actions/python-setup/pip@v1
  with:
    cache: 'pip'
```

### Error: "Invalid requirement: '.[dev][test]'"

**Cause**: This was a bug in earlier versions (now fixed). Multiple groups were generating `.[dev][test]` instead of `.[dev,test]`.

**Solution**: Use the latest version of the action (`@v1` or later).

### Error: "UnicodeEncodeError: 'charmap' codec can't encode character"

**Cause**: Windows default encoding (cp1252) doesn't support Unicode characters in Python print statements.

**Solution**: Use `shell: bash` and avoid Unicode characters:
```yaml
- name: Test
  shell: bash
  run: python -c "print('[OK] Test passed')"  # Not: print('✓ Test passed')
```

### Dependencies Not Installing

**Symptoms**: Action succeeds but packages are missing.

**Debug Steps**:

1. Check if `pyproject.toml` exists:
```yaml
- run: ls -la
- run: cat pyproject.toml
```

2. Verify action output in logs (look for "Installing dependencies" group):
```
Found pyproject.toml, installing package...
Installing with dependency groups: dev test
Running: pip install .[dev,test]
```

3. Check installed packages:
```yaml
- run: pip list
- run: pip show pytest  # Check specific package
```

### Cache Not Working

**Symptoms**: Dependencies reinstall on every run.

**Debug Steps**:

1. Verify cache is enabled:
```yaml
with:
  cache: 'pip'  # Must be explicitly set
```

2. Check cache hit in logs:
```
Cache restored from key: ...
```

3. Ensure dependencies file hasn't changed (cache key is based on file hash).

## Best Practices

### 1. Use Cache for Stable Dependencies

```yaml
# Good: Stable project with versioned dependencies
- uses: serapeum-org/github-actions/actions/python-setup/pip@v1
  with:
    cache: 'pip'
```

### 2. Pin Dependency Versions in pyproject.toml

```toml
# Good: Specific versions for reproducible builds
dependencies = [
  "requests==2.31.0",
  "numpy>=1.26.0,<2.0.0"
]

# Avoid: Unpinned versions can break builds
dependencies = ["requests", "numpy"]
```

### 3. Separate Dependency Groups by Purpose

```toml
[project.optional-dependencies]
# Good: Logical separation
dev = ["black", "mypy", "ruff"]
test = ["pytest", "pytest-cov", "pytest-mock"]
docs = ["mkdocs", "mkdocs-material"]

# Avoid: Single group for everything
dev = ["black", "mypy", "pytest", "mkdocs"]
```

### 4. Use Matrix Testing for Library Projects

```yaml
# Libraries should test against multiple Python versions
strategy:
  matrix:
    python-version: ['3.10', '3.11', '3.12']

steps:
  - uses: serapeum-org/github-actions/actions/python-setup/pip@v1
    with:
      python-version: ${{ matrix.python-version }}
```

### 5. Disable Cache for Dynamic Dependencies

```yaml
# If dependencies change frequently (e.g., from git branches)
- uses: serapeum-org/github-actions/actions/python-setup/pip@v1
  # No cache parameter (defaults to '')
```

### 6. Use Specific Action Versions

```yaml
# Good: Pin to major version (gets bug fixes)
- uses: serapeum-org/github-actions/actions/python-setup/pip@v1

# Acceptable: Pin to exact commit (maximum stability)
- uses: serapeum-org/github-actions/actions/python-setup/pip@abc1234

# Avoid: Using @main (unpredictable)
- uses: serapeum-org/github-actions/actions/python-setup/pip@main
```

### 7. Combine with Other Actions

```yaml
- uses: actions/checkout@v5
- uses: serapeum-org/github-actions/actions/python-setup/pip@v1
  with:
    cache: 'pip'
    install-groups: 'test'

- name: Run tests with coverage
  run: pytest --cov=src --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v4
```

## Comparison with Other Actions

| Feature | This Action | actions/setup-python | astral-sh/setup-uv |
|---------|-------------|---------------------|-------------------|
| Python Installation | ✓ | ✓ | ✓ |
| Pip Caching | ✓ | ✓ | ✗ |
| Auto Pip Upgrade | ✓ | ✗ | N/A |
| Dependency Groups | ✓ | ✗ | ✓ |
| Cache Validation | ✓ | ✗ | ✗ |
| pyproject.toml Auto-install | ✓ | ✗ | ✓ |
| Package Summary | ✓ | ✗ | ✗ |
| Cross-platform | ✓ | ✓ | ✓ |

**When to use this action:**
- Standard pip-based projects
- Need dependency groups with pip
- Want automatic validation and error messages
- Need clear GitHub Actions log output

**When to use alternatives:**
- `actions/setup-python` alone: Minimal setup, no extras needed
- `astral-sh/setup-uv`: Modern projects wanting faster dependency resolution

## Migration Guide

### From actions/setup-python

**Before**:
```yaml
- uses: actions/setup-python@v6
  with:
    python-version: '3.12'
    cache: 'pip'
- run: pip install .
- run: pip install .[dev,test]
```

**After**:
```yaml
- uses: serapeum-org/github-actions/actions/python-setup/pip@v1
  with:
    python-version: '3.12'
    cache: 'pip'
    install-groups: 'dev test'
```

### From Manual Pip Commands

**Before**:
```yaml
- uses: actions/setup-python@v6
- run: python -m pip install --upgrade pip
- run: |
    if [ -f pyproject.toml ]; then
      pip install .[dev,test]
    fi
```

**After**:
```yaml
- uses: serapeum-org/github-actions/actions/python-setup/pip@v1
  with:
    cache: 'pip'
    install-groups: 'dev test'
```

## Additional Resources

- [GitHub Actions: actions/setup-python](https://github.com/actions/setup-python)
- [Python Packaging User Guide](https://packaging.python.org/)
- [PEP 621: pyproject.toml metadata](https://peps.python.org/pep-0621/)
- [pip documentation](https://pip.pypa.io/)

## Support

For issues, questions, or contributions:
- Repository: https://github.com/serapeum-org/github-actions
- Issues: https://github.com/serapeum-org/github-actions/issues
