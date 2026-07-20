te a# Python Setup with pixi - Complete Guide

Composite GitHub Action for setting up Python environments with the pixi package manager, designed for projects using conda-forge packages and cross-platform development with `pyproject.toml`.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Inputs Reference](#inputs-reference)
- [Features](#features)
- [Usage Scenarios](#usage-scenarios)
  - [Basic Setup](#basic-setup)
  - [Multiple Environments](#multiple-environments)
  - [Environment Activation](#environment-activation)
  - [Matrix Testing](#matrix-testing)
  - [Complex Projects with Features](#complex-projects-with-features)
  - [Caching](#caching)
- [Lock File Management](#lock-file-management)
  - [Lock File Verification](#lock-file-verification)
  - [Frozen vs Locked Modes](#frozen-vs-locked-modes)
- [Environment Architecture](#environment-architecture)
- [Caching Strategy](#caching-strategy)
- [Testing Guide](#testing-guide)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Overview

This action provides a complete Python environment setup using [pixi](https://prefix.dev/), a fast package manager built on top of conda. It automatically:

- Installs pixi package manager
- Validates lock file existence
- Sets up one or more pixi environments
- Activates a specified environment
- Optionally caches environments for faster CI runs
- Verifies lock file integrity (configurable)

**Key Features:**
- ✅ Support for conda-forge and other conda channels
- ✅ Cross-platform compatibility (Linux, macOS, Windows)
- ✅ Multiple environment support
- ✅ Feature-based dependency management
- ✅ Intelligent caching with lock file validation
- ✅ Lock file verification modes (locked/frozen)

**Location**: `serapeum-org/github-actions/actions/python-setup/pixi@v1`

## Quick Start

### Basic Usage (Default Environment)

```yaml
steps:
  - uses: actions/checkout@v5
  - uses: serapeum-org/github-actions/actions/python-setup/pixi@v1

  # The default environment is automatically activated!
  - run: python --version
  - run: pytest
```

### With Multiple Environments

```yaml
steps:
  - uses: actions/checkout@v5
  - uses: serapeum-org/github-actions/actions/python-setup/pixi@v1
    with:
      environments: 'dev test prod'
      activate-environment: 'dev'

  - run: pytest  # Runs in dev environment
```

### With Caching Enabled

```yaml
steps:
  - uses: actions/checkout@v5
  - uses: serapeum-org/github-actions/actions/python-setup/pixi@v1
    with:
      cache: 'true'

  - run: python --version  # Much faster on subsequent runs!
```

## Inputs Reference

| Input | Description | Required | Default | Valid Values |
|-------|-------------|----------|---------|--------------|
| `environments` | Pixi environments to install | No | `'default'` | Space-separated list (e.g., `'py311'`, `'dev test prod'`) |
| `activate-environment` | Environment to activate after installation | No | `'default'` | Any environment name from your `pyproject.toml` |
| `cache` | Enable caching of pixi environments | No | `'false'` | `'true'`, `'false'` |
| `verify-lock` | Verify lock file is up to date | No | `'true'` | `'true'`, `'false'` |
| `version` | Version of pixi to install | No | `'latest'` | Release tag (e.g., `'v0.65.0'`) or `'latest'` |

### Input Details

#### `environments`
Specifies which pixi environments from `[tool.pixi.environments]` in `pyproject.toml` to install.

**Default behavior (`'default'`)**: Installs only the default environment.

**When specified**: Installs all specified environments. This is useful when you need to prepare multiple environments or when running matrix tests.

**Formats supported:**
- Single environment: `'dev'`
- Space-separated: `'dev test prod'`
- Multiple runs: You can call the action multiple times with different environments (though not recommended - see best practices)

**Example `pyproject.toml`:**
```toml
[tool.pixi.environments]
default = ["core"]
dev = ["core", "dev-tools"]
test = ["core", "test-tools"]
prod = ["core"]
```

**Usage:**
```yaml
# Install only dev environment
environments: 'dev'

# Install dev and test environments
environments: 'dev test'

# Install all environments
environments: 'default dev test prod'
```

#### `activate-environment`
Specifies which environment to activate in the GitHub Actions PATH after installation.

**Default behavior (`'default'`)**: Activates the default environment.

**Important**: This should be ONE of the environments listed in the `environments` input. If you specify an environment that wasn't installed, the action will fail.

**Example:**
```yaml
# Install multiple environments but activate only 'dev'
with:
  environments: 'dev test prod'
  activate-environment: 'dev'
```

After activation:
- Python and packages from the activated environment are available in PATH
- All subsequent steps use this environment
- You can run `pixi run -e <env>` to run commands in other environments

#### `cache`
Controls whether to cache the pixi environments directory (`.pixi`) for faster CI runs.

**Default: `'false'`** - No caching by default to ensure clean environments unless explicitly requested.

**When `'true'`**:
- Caches the `.pixi` directory based on `pixi.lock` hash
- Cache is only written on `push` events to the `main` branch
- Significantly speeds up subsequent CI runs (from minutes to seconds)
- **Requires `pixi.lock` file** - will fail with a clear error if missing

**Cache key structure**: `pixi-<hash-of-pixi.lock>`

**Cache write behavior**: Only writes cache when:
- `cache: 'true'` is set
- Event is `push` (not PR)
- Branch is `main`

**Example:**
```yaml
# Enable caching (recommended for production)
cache: 'true'

# Disable caching (useful for debugging)
cache: 'false'
```

#### `verify-lock`
Controls lock file verification behavior and pixi installation mode.

**Default: `'true'`** - Always verify lock file is up to date.

**When `'true'` (locked mode)**:
- Uses `pixi install --locked`
- Verifies that `pixi.lock` matches `pyproject.toml`
- **Fails if lock file is outdated** - prevents installing mismatched dependencies
- Recommended for CI/CD to catch lock file drift

**When `'false'` (frozen mode)**:
- Uses `pixi install --frozen`
- Uses lock file as-is without verification
- Faster but won't catch outdated lock files
- Useful when you're certain the lock file is correct

**Example:**
```yaml
# Verify lock file (default, recommended for CI)
verify-lock: 'true'

# Skip verification (faster, use cautiously)
verify-lock: 'false'
```

#### `version`
Selects the pixi release installed by `prefix-dev/setup-pixi` (forwarded as its `pixi-version` input).

**Default (`'latest'`)**: Installs the newest pixi release.

Pin a specific release tag for reproducible runs, or keep `'latest'` for the newest release:

```yaml
# Pin a specific pixi version (recommended for reproducibility)
version: 'v0.65.0'

# Always use the newest pixi release
version: 'latest'
```

**Note**: Pass the tag exactly as published by pixi, including the leading `v` (e.g. `'v0.65.0'`). The pinned
version must be able to read your committed `pixi.lock` format.

**Breaking change (`pixi/v1`)**: Earlier releases of this action always installed a pinned pixi `v0.65.0`. It now
defaults to `version: 'latest'`, so existing `pixi/v1` consumers that do not set `version` will start getting the
newest pixi resolved against their committed `pixi.lock`. To keep the previous behavior, pin `version: 'v0.65.0'`.

## Features

### 1. Automatic Lock File Validation

The action **always requires a `pixi.lock` file** to be present in your repository. This ensures reproducible builds across all environments.

**What happens:**
1. ✅ Checks if `pixi.lock` exists
2. ❌ Fails with a clear error message if missing
3. 📝 Provides instructions on how to generate the lock file locally

**Error message when lock file is missing:**
```
❌ pixi.lock file does not exist!
To fix this issue:
 Run 'pixi install' locally to generate pixi.lock and commit it to your repository
This action requires a committed lock file and will never generate it in CI.
```

**Why this design?**
- Lock files should be generated on the developer's machine, not in CI
- Ensures all developers and CI use the same dependency versions
- Prevents CI from making commits or masking dependency conflicts
- Makes dependency updates explicit and reviewable

### 2. Dual Mode Installation: Locked vs Frozen

The action supports two installation modes controlled by the `verify-lock` input:

**Locked Mode (`verify-lock: 'true'` - default):**
```bash
pixi install --locked
```
- Verifies `pixi.lock` matches `pyproject.toml`
- Fails if dependencies were added/removed without updating lock file
- **Best for**: CI/CD pipelines, ensuring strict reproducibility

**Frozen Mode (`verify-lock: 'false'`):**
```bash
pixi install --frozen
```
- Uses `pixi.lock` without verification
- Faster but won't detect lock file drift
- **Best for**: Local development, trusted environments

**Comparison:**

| Mode | Flag | Verifies Lock | Speed | Use Case |
|------|------|---------------|-------|----------|
| Locked | `--locked` | ✅ Yes | Slower | CI/CD, production |
| Frozen | `--frozen` | ❌ No | Faster | Development, trusted deploys |

### 3. Environment Information Logging

After installation, the action automatically logs environment information:

**Pixi Information:**
```
Active environment: dev
Available environments:
  - default
  - dev
  - test
  - prod
```

**Installed Packages:**
```
Installed packages summary:
  python 3.11.7
  numpy 1.26.2
  pandas 2.1.4
  pytest 7.4.3
  ...
```

This appears in collapsible sections in GitHub Actions logs for easy debugging.

### 4. Intelligent Caching

When `cache: 'true'` is enabled:

**Cache Behavior:**
- **Key**: `pixi-<hash(pixi.lock)>`
- **Cached**: `.pixi/` directory (all environments)
- **Write**: Only on `push` to `main` branch
- **Read**: All runs (including PRs)

**Performance Impact:**
- 🐌 First run: ~5-10 minutes (install all packages)
- 🚀 Cached run: ~30 seconds (restore cache + verification)

**Cache Invalidation:**
- Automatic when `pixi.lock` changes
- Manual: bump version in `pyproject.toml` or clear GitHub cache

### 5. Cross-Platform Support

The action works seamlessly across:
- 🐧 **Linux** (ubuntu-latest)
- 🍎 **macOS** (macos-latest, macos-13, macos-14)
- 🪟 **Windows** (windows-latest)

Shell commands automatically adapt to the platform (bash on Linux/macOS, PowerShell on Windows).

### 6. Multiple Environment Management

Install and manage multiple environments in a single workflow:

```yaml
- uses: serapeum-org/github-actions/actions/python-setup/pixi@v1
  with:
    environments: 'py311 py312 py313'
    activate-environment: 'py311'

# py311 is active by default
- run: python --version  # Python 3.11

# Switch to another environment for specific commands
- run: pixi run -e py312 python --version  # Python 3.12
- run: pixi run -e py313 pytest  # Run tests in Python 3.13
```

## Usage Scenarios

### Basic Setup

**Scenario**: Simple project with a single environment.

**`pyproject.toml`:**
```toml
[project]
name = "my-project"
version = "0.1.0"

[tool.pixi.workspace]
channels = ["conda-forge"]
platforms = ["linux-64", "osx-64", "win-64"]

[tool.pixi.dependencies]
python = ">=3.11"
numpy = ">=1.26"
pytest = ">=7.0"
```

**Workflow:**
```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      
      - name: Setup Python with pixi
        uses: serapeum-org/github-actions/actions/python-setup/pixi@v1
        with:
          cache: 'false'
      
      - name: Run tests
        run: pytest
      
      - name: Verify installation
        run: |
          python --version
          python -c "import numpy; print(f'NumPy {numpy.__version__}')"
```

**Result**: Default environment is installed and activated, all packages available.

### Multiple Environments

**Scenario**: Project with separate development and production environments.

**`pyproject.toml`:**
```toml
[tool.pixi.workspace]
channels = ["conda-forge"]
platforms = ["linux-64", "osx-64", "win-64"]

[tool.pixi.dependencies]
python = ">=3.11"

[tool.pixi.feature.core.dependencies]
numpy = ">=1.26"
pandas = ">=2.0"

[tool.pixi.feature.dev.dependencies]
pytest = ">=7.0"
black = ">=23.0"
ruff = ">=0.1"

[tool.pixi.feature.prod.dependencies]
gunicorn = ">=21.0"

[tool.pixi.environments]
default = ["core"]
dev = ["core", "dev"]
prod = ["core", "prod"]
```

**Workflow:**
```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      
      - name: Setup dev environment
        uses: serapeum-org/github-actions/actions/python-setup/pixi@v1
        with:
          environments: 'dev'
          activate-environment: 'dev'
          cache: 'false'
      
      - name: Run linting
        run: |
          black --check .
          ruff check .
      
      - name: Run tests
        run: pytest

  deploy-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      
      - name: Setup prod environment
        uses: serapeum-org/github-actions/actions/python-setup/pixi@v1
        with:
          environments: 'prod'
          activate-environment: 'prod'
          cache: 'false'
      
      - name: Verify prod dependencies
        run: |
          python -c "import gunicorn"
          python -c "import numpy, pandas"
```

**Result**: Different jobs use different environments with appropriate dependencies.

### Environment Activation

**Scenario**: Install multiple environments but work primarily in one.

**`pyproject.toml`:**
```toml
[tool.pixi.feature.core.dependencies]
python = ">=3.11"
requests = ">=2.31"

[tool.pixi.feature.dev.dependencies]
pytest = ">=7.0"
black = ">=23.0"

[tool.pixi.feature.test.dependencies]
pytest = ">=7.0"
pytest-cov = ">=4.0"
hypothesis = ">=6.0"

[tool.pixi.environments]
default = ["core"]
dev = ["core", "dev"]
test = ["core", "test"]
```

**Workflow:**
```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      
      - name: Setup all environments
        uses: serapeum-org/github-actions/actions/python-setup/pixi@v1
        with:
          environments: 'dev test'
          activate-environment: 'dev'  # Dev is active by default
          cache: 'false'
      
      - name: Run linting (uses active dev environment)
        run: black --check .
      
      - name: Run tests (switch to test environment)
        run: pixi run -e test pytest --cov
      
      - name: Check coverage (in test environment)
        run: pixi run -e test coverage report
```

**Result**: Multiple environments available, explicit control over which is active.

### Matrix Testing

**Scenario**: Test across multiple Python versions or OS combinations.

**`pyproject.toml`:**
```toml
[tool.pixi.workspace]
channels = ["conda-forge"]
platforms = ["linux-64", "osx-64", "osx-arm64", "win-64"]

[tool.pixi.dependencies]
python = ">=3.11"

[tool.pixi.feature.py311.dependencies]
python = "3.11.*"
pandas = ">=2.0"

[tool.pixi.feature.py312.dependencies]
python = "3.12.*"
scikit-learn = ">=1.3"

[tool.pixi.environments]
default = []
py311 = ["py311"]
py312 = ["py312"]
```

**Workflow:**
```yaml
jobs:
  test-matrix:
    name: Test Python ${{ matrix.python-env }} on ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-env: ['py311', 'py312']
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v5
      
      - name: Setup Python environment
        uses: serapeum-org/github-actions/actions/python-setup/pixi@v1
        with:
          environments: ${{ matrix.python-env }}
          activate-environment: ${{ matrix.python-env }}
          cache: 'false'
      
      - name: Run tests
        run: |
          python --version
          pytest
```

**Result**: Tests run on 6 combinations (3 OS × 2 Python versions), each with correct environment.

### Complex Projects with Features

**Scenario**: Large project with multiple feature sets (ML, visualization, development tools).

**`pyproject.toml`:**
```toml
[project]
name = "complex-ml-project"
version = "0.1.0"

[tool.pixi.workspace]
channels = ["conda-forge", "pytorch"]
platforms = ["linux-64", "osx-64", "osx-arm64", "win-64"]

[tool.pixi.tasks]
test = "pytest tests/"
lint = "ruff check ."
train = "python scripts/train.py"

[tool.pixi.dependencies]
python = ">=3.11,<3.13"

[tool.pixi.feature.core.dependencies]
numpy = ">=1.26"
pandas = ">=2.0"
scipy = ">=1.11"

[tool.pixi.feature.ml.dependencies]
scikit-learn = ">=1.3"
xgboost = ">=2.0"
pytorch = ">=2.0"

[tool.pixi.feature.viz.dependencies]
matplotlib = ">=3.8"
seaborn = ">=0.13"
plotly = ">=5.18"

[tool.pixi.feature.dev.dependencies]
pytest = ">=7.0"
pytest-cov = ">=4.0"
black = ">=23.0"
ruff = ">=0.1"
mypy = ">=1.0"

[tool.pixi.environments]
default = ["core", "dev"]
ml = ["core", "ml", "viz", "dev"]
prod = ["core", "ml"]
ci = ["core", "ml", "dev"]
```

**Workflow:**
```yaml
jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      
      - name: Setup CI environment
        uses: serapeum-org/github-actions/actions/python-setup/pixi@v1
        with:
          environments: 'ci'
          activate-environment: 'ci'
          cache: 'true'  # Enable caching for complex environments
      
      - name: Lint code
        run: |
          black --check .
          ruff check .
          mypy src/
      
      - name: Run tests
        run: pytest --cov=src tests/
      
      - name: Test ML models
        run: |
          python -c "import sklearn, xgboost, torch"
          python scripts/test_model.py

  train-model:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      
      - name: Setup ML environment
        uses: serapeum-org/github-actions/actions/python-setup/pixi@v1
        with:
          environments: 'ml'
          activate-environment: 'ml'
          cache: 'true'
      
      - name: Train model
        run: python scripts/train.py
      
      - name: Generate visualizations
        run: python scripts/visualize.py
```

**Result**: Different jobs use optimized environments with only necessary dependencies.

### Caching

**Scenario**: Speed up CI by caching the pixi environment.

#### Without Caching

**Workflow:**
```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      
      - name: Setup Python
        uses: serapeum-org/github-actions/actions/python-setup/pixi@v1
        with:
          cache: 'false'  # No caching
      
      - name: Run tests
        run: pytest
```

**Time**: ~5-10 minutes per run (full package installation each time)

#### With Caching

**Workflow:**
```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      
      - name: Setup Python with caching
        uses: serapeum-org/github-actions/actions/python-setup/pixi@v1
        with:
          cache: 'true'  # Enable caching
      
      - name: Run tests
        run: pytest
```

**Time**:
- First run: ~5-10 minutes (installs packages + saves cache)
- Subsequent runs: ~30 seconds (restores cache)
- After lock file change: ~5-10 minutes (cache miss, rebuilds)

**Cache behavior:**
- ✅ **Reads cache**: All runs (PRs, pushes, manual)
- ✏️ **Writes cache**: Only on `push` to `main` branch
- 🔄 **Updates cache**: When `pixi.lock` changes

#### Validation Without Lock File

The action will fail if you enable caching without a lock file:

**Workflow (will fail):**
```yaml
- name: Setup Python with caching
  uses: serapeum-org/github-actions/actions/python-setup/pixi@v1
  with:
    cache: 'true'  # ❌ Will fail - no pixi.lock!
```

**Error:**
```
❌ Cache is enabled but pixi.lock file does not exist!
To fix this issue:
 First run 'pixi install' locally to generate pixi.lock and then commit it to your repository
```

**How to fix:**
```bash
# On your local machine
pixi install  # Generates pixi.lock
git add pixi.lock
git commit -m "Add pixi lock file"
git push
```

## Lock File Management

### Lock File Verification

The action implements a **lock-file-first** approach:

1. **Lock file is mandatory**: Action fails immediately if `pixi.lock` doesn't exist
2. **Generated locally**: Developers run `pixi install` on their machines
3. **Committed to repository**: Lock file is version-controlled
4. **Verified in CI**: Action validates (optionally) that lock matches dependencies

**Benefits:**
- 🔒 **Reproducibility**: Everyone uses exact same versions
- 👀 **Visibility**: Lock file changes are reviewable in PRs
- 🚫 **No surprises**: CI doesn't install different versions than local
- ⚡ **Speed**: No lock resolution in CI

### Frozen vs Locked Modes

The `verify-lock` input controls how pixi uses the lock file:

#### Locked Mode (`verify-lock: 'true'` - Default)

**Command used**: `pixi install --locked`

**Behavior:**
1. Reads `pixi.lock`
2. Compares with `pyproject.toml`
3. ❌ **Fails if mismatch** (dependencies added/changed without updating lock)
4. ✅ Installs exact versions from lock file

**Use when:**
- Running CI/CD pipelines
- You want strict reproducibility
- You want to catch lock file drift

**Example:**
```yaml
- name: Setup with verification
  uses: serapeum-org/github-actions/actions/python-setup/pixi@v1
  with:
    verify-lock: 'true'  # Default
```

**What it catches:**
```toml
# pyproject.toml - added pandas
[tool.pixi.dependencies]
python = ">=3.11"
numpy = ">=1.26"
pandas = ">=2.0"  # ⚠️ NEW!

# pixi.lock - doesn't have pandas
# ❌ Action fails: "Lock file is outdated!"
```

#### Frozen Mode (`verify-lock: 'false'`)

**Command used**: `pixi install --frozen`

**Behavior:**
1. Reads `pixi.lock`
2. Installs exact versions from lock file
3. ✅ **No verification** - trusts lock file is correct
4. Faster (skips verification step)

**Use when:**
- You're certain the lock file is up to date
- You want faster CI runs
- Lock file is updated automatically by bots/tools

**Example:**
```yaml
- name: Setup without verification
  uses: serapeum-org/github-actions/actions/python-setup/pixi@v1
  with:
    verify-lock: 'false'
```

**Warning**: Won't catch lock file drift, so use carefully.

#### Comparison Table

| Aspect | Locked Mode | Frozen Mode |
|--------|-------------|-------------|
| **Command** | `--locked` | `--frozen` |
| **Verifies lock** | ✅ Yes | ❌ No |
| **Fails on drift** | ✅ Yes | ❌ No |
| **Speed** | Slower (verification) | Faster |
| **Safety** | Safer | Less safe |
| **Best for** | CI/CD | Trusted environments |
| **Default** | ✅ Yes | No |

#### When to Use Each Mode

**Use Locked Mode (`verify-lock: 'true'`) when:**
- ✅ Running CI/CD pipelines
- ✅ Multiple contributors updating dependencies
- ✅ You want to enforce lock file updates
- ✅ Security is important (catch unexpected changes)

**Use Frozen Mode (`verify-lock: 'false'`) when:**
- ✅ Lock file is auto-updated (Dependabot, Renovate)
- ✅ Single developer project
- ✅ Speed is critical (many CI runs)
- ✅ You have other verification mechanisms

#### Updating Lock Files

**Recommended workflow:**

1. **Update dependencies locally:**
   ```bash
   # Edit pyproject.toml
   vim pyproject.toml
   
   # Update lock file
   pixi install
   
   # Verify it works
   pixi run pytest
   ```

2. **Commit both files:**
   ```bash
   git add pyproject.toml pixi.lock
   git commit -m "Update numpy to 2.0"
   git push
   ```

3. **CI validates:**
   - PR runs with `verify-lock: 'true'`
   - ✅ Passes because lock file matches
   - Reviewers see both files changed

**What NOT to do:**
```bash
# ❌ Don't edit only pyproject.toml without updating lock
vim pyproject.toml
git add pyproject.toml  # Missing pixi.lock!
git commit -m "Update numpy"
# CI will fail with "Lock file is outdated"
```

## Environment Architecture

### Understanding Pixi Environments

Pixi uses a feature-based system to compose environments:

**Features** → **Environments** → **Activation**

#### 1. Features (Dependency Groups)

Features define groups of related dependencies:

```toml
[tool.pixi.feature.core.dependencies]
python = ">=3.11"
numpy = ">=1.26"

[tool.pixi.feature.dev.dependencies]
pytest = ">=7.0"
black = ">=23.0"

[tool.pixi.feature.ml.dependencies]
scikit-learn = ">=1.3"
pytorch = ">=2.0"
```

**Think of features as:**
- 📦 Reusable dependency sets
- 🧩 Building blocks for environments
- 🎯 Logical groupings (core, dev, ML, viz, etc.)

#### 2. Environments (Feature Combinations)

Environments combine multiple features:

```toml
[tool.pixi.environments]
default = ["core"]                    # Just core
dev = ["core", "dev"]                 # Core + dev tools
ml = ["core", "ml"]                   # Core + ML packages
full = ["core", "dev", "ml"]          # Everything
```

**Think of environments as:**
- 🎭 Different use cases (dev, test, prod)
- 🔧 Job-specific setups
- 📊 Matrix test configurations

#### 3. Activation (Runtime Selection)

The action installs environments and activates one:

```yaml
environments: 'dev ml'           # Installs both
activate-environment: 'dev'      # Activates dev (adds to PATH)
```

**After activation:**
- ✅ `python` → Python from activated environment
- ✅ `pytest` → If in activated environment
- ✅ Package imports work from activated environment
- ❌ Packages from other environments not in PATH (but can use `pixi run -e`)

### Environment Lifecycle

**Step-by-step what happens:**

1. **Validation**: Check `pixi.lock` exists
2. **Installation**: Install pixi (if not cached)
3. **Lock Check** (if `verify-lock: 'true'`): Verify lock matches pyproject.toml
4. **Environment Creation**: Install specified environments
   ```bash
   pixi install --locked  # or --frozen
   # Creates .pixi/envs/dev/, .pixi/envs/ml/, etc.
   ```
5. **Activation**: Add environment to PATH
   ```bash
   # Adds .pixi/envs/dev/bin to PATH
   ```
6. **Verification**: Log environment info

### Directory Structure

After installation, your project looks like:

```
my-project/
├── pyproject.toml
├── pixi.lock
├── .pixi/                      # Created by pixi
│   ├── envs/
│   │   ├── default/            # Each environment
│   │   │   ├── bin/
│   │   │   ├── lib/
│   │   │   └── ...
│   │   ├── dev/
│   │   │   ├── bin/
│   │   │   └── ...
│   │   └── ml/
│   │       └── ...
│   └── bin/
│       └── pixi                # Pixi binary
├── src/
└── tests/
```

**Caching caches**: The entire `.pixi/` directory

## Caching Strategy

### How Caching Works

**Cache Key**: `pixi-<hash(pixi.lock)>`

**What's cached**: Entire `.pixi/` directory containing:
- All installed environments
- Pixi binary
- Package metadata

**Cache flow:**

```
┌─────────────────┐
│  Run starts     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Hash pixi.lock  │ ← Generate cache key
└────────┬────────┘
         │
         ▼
    ┌────────┐
    │ Cache  │
    │ hit?   │
    └───┬────┘
        │
    ┌───┴────┐
    │        │
   YES      NO
    │        │
    ▼        ▼
┌────────┐ ┌──────────────┐
│Restore │ │Install fresh │
│cache   │ │              │
└───┬────┘ └──────┬───────┘
    │             │
    │             ▼
    │      ┌──────────────┐
    │      │ Is push to   │
    │      │ main branch? │
    │      └──────┬───────┘
    │             │
    │         ┌───┴───┐
    │         │       │
    │        YES     NO
    │         │       │
    │         ▼       ▼
    │   ┌─────────┐ ┌────────┐
    │   │  Save   │ │  Skip  │
    │   │  cache  │ │  save  │
    │   └─────────┘ └────────┘
    │
    └──────────┬──────────────┘
               │
               ▼
         ┌──────────┐
         │   Done   │
         └──────────┘
```

### Cache Performance

**Typical timings:**

| Scenario | Time | Notes |
|----------|------|-------|
| **No cache, small project** | 1-2 min | Few packages |
| **No cache, large project** | 5-10 min | Many packages (ML libs) |
| **Cache hit** | 20-40 sec | Restore + verify |
| **Cache miss** | 5-10 min | Full install + save |

**Factors affecting speed:**
- Number of packages
- Package size (pytorch is large!)
- Number of environments
- Network speed (first install)

### Cache Invalidation

**Automatic invalidation when:**
- ✅ `pixi.lock` changes (new hash → new key)
- ✅ GitHub clears old caches (7 days unused)

**Manual invalidation:**
- Clear cache via GitHub UI (Settings → Actions → Caches)
- Change cache key (modify action or add version to `pyproject.toml`)

**Cache won't invalidate when:**
- ❌ Only `pyproject.toml` changes (lock file unchanged)
- ❌ Code changes
- ❌ Non-dependency configuration changes

### Cache Best Practices

**DO:**
- ✅ Enable caching for stable projects
- ✅ Use caching in production CI
- ✅ Monitor cache hit rates
- ✅ Include lock file in commits

**DON'T:**
- ❌ Enable caching when debugging dependency issues
- ❌ Rely on cache without lock file verification
- ❌ Cache in fork PRs (limited cache space)

**Optimal configuration:**
```yaml
# Main branch - write cache
- uses: serapeum-org/github-actions/actions/python-setup/pixi@v1
  with:
    cache: 'true'
    verify-lock: 'true'  # Verify even with cache

# PR branches - read cache only (automatic)
# Same configuration, but cache-write is disabled automatically
```

## Testing Guide

This action is comprehensively tested across multiple scenarios to ensure reliability. Reference the test workflow at `.github/workflows/test-python-setup-pixi.yml`.

### Test Coverage Matrix

| Test Job | Purpose | Key Validations | Fixture |
|----------|---------|-----------------|---------|
| `test-pixi-basic` | Default behavior | Pixi and Python installed, packages available | `test-pixi-basic/` |
| `test-pixi-default-environment` | Default environment only | Only default environment installed | `test-pixi-default-environment/` |
| `test-pixi-multiple-environments` | Multiple environments | Multiple envs installed, correct one activated | `test-pixi-multiple-environments/` |
| `test-pixi-environment-activation` | Environment activation | Specific environment activated correctly | `test-pixi-environment-activation/` |
| `test-pixi-lock-verification-valid` | Valid lock file | Lock verification passes | `test-pixi-lock-verification-valid/` |
| `test-pixi-lock-verification-outdated` | Outdated lock handling | Fails with outdated lock file | `test-pixi-lock-verification-outdated/` |
| `test-pixi-lock-verification-disabled` | Skip lock check | Works with `verify-lock: 'false'` | `test-pixi-lock-verification-disabled/` |
| `test-pixi-lock-verification-validation` | Missing lock file | Fails without lock file | `test-pixi-lock-verification-validation/` |
| `test-pixi-caching-populate` | Cache population | Cache created and packages installed | `test-pixi-caching-populate/` |
| `test-pixi-caching-retrieve` | Cache retrieval | Cache restored on subsequent runs | `test-pixi-caching-retrieve/` |
| `test-pixi-caching-validation` | Cache without lock | Fails when cache enabled without lock | - |
| `test-pixi-matrix` | Cross-platform matrix | Works on Linux/Windows/macOS with multiple environments | `test-pixi-matrix/` |
| `test-pixi-error-scenarios` | Error handling | Proper errors for missing lock, wrong environment | `test-pixi-basic/` |
| `test-pixi-complex-project` | Complex setup | Multiple features and environments | `test-pixi-complex-project/` |

### Test Fixtures Location

All test fixtures are located in `tests/data/pixi/` directory:
```
tests/data/pixi/
├── test-pixi-basic/
│   ├── pyproject.toml
│   └── pixi.lock
├── test-pixi-default-environment/
│   ├── pyproject.toml
│   └── pixi.lock
├── test-pixi-multiple-environments/
│   ├── pyproject.toml
│   └── pixi.lock
├── test-pixi-environment-activation/
│   ├── pyproject.toml
│   └── pixi.lock
├── test-pixi-lock-verification-valid/
│   ├── pyproject.toml
│   └── pixi.lock
├── test-pixi-lock-verification-outdated/
│   ├── pyproject.toml
│   └── pixi.lock
├── test-pixi-lock-verification-disabled/
│   ├── pyproject.toml
│   └── pixi.lock
├── test-pixi-lock-verification-validation/
│   └── pyproject.toml  # No lock file (intentional)
├── test-pixi-caching-populate/
│   ├── pyproject.toml
│   └── pixi.lock
├── test-pixi-caching-retrieve/
│   ├── pyproject.toml
│   └── pixi.lock
├── test-pixi-matrix/
│   ├── pyproject.toml
│   └── pixi.lock
└── test-pixi-complex-project/
    ├── pyproject.toml
    └── pixi.lock
```

### Example Test Fixtures

**test-pixi-basic/pyproject.toml:**
```toml
[project]
name = "test-pixi-basic"
version = "0.1.0"
dependencies = []

[tool.pixi.workspace]
channels = ["conda-forge"]
platforms = ["linux-64", "osx-64", "osx-arm64", "win-64"]

[tool.pixi.dependencies]
python = ">=3.11"
numpy = ">=1.26"
pytest = ">=7.0"
```

**test-pixi-multiple-environments/pyproject.toml:**
```toml
[project]
name = "test-multi-env"
version = "0.1.0"

[tool.pixi.workspace]
channels = ["conda-forge"]
platforms = ["linux-64", "osx-64", "osx-arm64", "win-64"]

[tool.pixi.feature.core.dependencies]
python = ">=3.11"
numpy = ">=1.26"

[tool.pixi.feature.py311.dependencies]
python = "3.11.*"
pandas = ">=2.0"

[tool.pixi.feature.py312.dependencies]
python = "3.12.*"
pandas = ">=2.0"

[tool.pixi.environments]
default = ["core"]
py311 = ["core", "py311"]
py312 = ["core", "py312"]
```

**test-pixi-complex-project/pyproject.toml:**
```toml
[project]
name = "test-complex"
version = "0.1.0"

[tool.pixi.workspace]
channels = ["conda-forge"]
platforms = ["linux-64", "osx-64", "osx-arm64", "win-64"]

[tool.pixi.feature.core.dependencies]
python = ">=3.11"
requests = ">=2.31"

[tool.pixi.feature.ml.dependencies]
numpy = ">=1.26"
scikit-learn = ">=1.3"

[tool.pixi.feature.dev.dependencies]
pytest = ">=7.0"
black = ">=23.0"

[tool.pixi.environments]
default = ["core", "dev"]
ml = ["core", "ml", "dev"]
prod = ["core", "ml"]
```

### Basic Test Setup

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      
      - uses: serapeum-org/github-actions/actions/python-setup/pixi@v1
        with:
          cache: 'false'
      
      - run: pytest tests/
```

### Matrix Testing: Multiple Python Versions

```yaml
jobs:
  test:
    strategy:
      matrix:
        python-env: ['py310', 'py311', 'py312']
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      
      - uses: serapeum-org/github-actions/actions/python-setup/pixi@v1
        with:
          environments: ${{ matrix.python-env }}
          activate-environment: ${{ matrix.python-env }}
          cache: 'false'
      
      - run: pytest
```

### Matrix Testing: Multiple Operating Systems

```yaml
jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v5
      
      - uses: serapeum-org/github-actions/actions/python-setup/pixi@v1
        with:
          cache: 'false'
      
      - run: pytest
```

### Matrix Testing: Combined

```yaml
jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-env: ['py311', 'py312']
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v5
      
      - uses: serapeum-org/github-actions/actions/python-setup/pixi@v1
        with:
          environments: ${{ matrix.python-env }}
          activate-environment: ${{ matrix.python-env }}
          cache: 'false'
      
      - run: pytest
```

### Testing Multiple Environments in One Job

```yaml
jobs:
  test-all:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      
      - uses: serapeum-org/github-actions/actions/python-setup/pixi@v1
        with:
          environments: 'dev test'
          activate-environment: 'dev'
          cache: 'false'
      
      - name: Lint with dev environment
        run: |
          black --check .
          ruff check .
      
      - name: Test with test environment
        run: pixi run -e test pytest --cov
```

### Lock File Verification Tests

#### Test Valid Lock File

```yaml
jobs:
  test-valid-lock:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      
      - uses: serapeum-org/github-actions/actions/python-setup/pixi@v1
        with:
          verify-lock: 'true'  # Should pass
          cache: 'false'
      
      - run: pytest
```

#### Test Outdated Lock File (Should Fail)

```yaml
jobs:
  test-outdated-lock:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      
      # Modify pyproject.toml to make lock outdated
      - run: |
          echo "" >> pyproject.toml
          echo "[tool.pixi.dependencies]" >> pyproject.toml
          echo "newpackage = \">=1.0\"" >> pyproject.toml
      
      - uses: serapeum-org/github-actions/actions/python-setup/pixi@v1
        id: setup
        continue-on-error: true
        with:
          verify-lock: 'true'  # Should fail
          cache: 'false'
      
      - name: Verify it failed
        if: steps.setup.outcome != 'failure'
        run: |
          echo "ERROR: Should have failed with outdated lock"
          exit 1
```

#### Test Without Lock File (Should Fail)

```yaml
jobs:
  test-no-lock:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      
      - run: rm pixi.lock  # Remove lock file
      
      - uses: serapeum-org/github-actions/actions/python-setup/pixi@v1
        id: setup
        continue-on-error: true
        with:
          cache: 'false'
      
      - name: Verify it failed
        if: steps.setup.outcome != 'failure'
        run: |
          echo "ERROR: Should have failed without lock file"
          exit 1
```

### Caching Tests

#### Test Cache Population

```yaml
jobs:
  cache-populate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      
      - uses: serapeum-org/github-actions/actions/python-setup/pixi@v1
        with:
          cache: 'true'
      
      - run: pytest
```

#### Test Cache Retrieval

```yaml
jobs:
  cache-populate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      
      - uses: serapeum-org/github-actions/actions/python-setup/pixi@v1
        with:
          cache: 'true'
      
      - run: pytest

  cache-retrieve:
    runs-on: ubuntu-latest
    needs: cache-populate
    steps:
      - uses: actions/checkout@v5
      
      - uses: serapeum-org/github-actions/actions/python-setup/pixi@v1
        id: setup
        with:
          cache: 'true'
      
      # Second run should be much faster
      - run: pytest
```

## Troubleshooting

### Common Issues

#### Issue: "pixi.lock file does not exist"

**Error message:**
```
❌ pixi.lock file does not exist!
To fix this issue:
 Run 'pixi install' locally to generate pixi.lock and commit it to your repository
```

**Solution:**
```bash
# On your local machine
pixi install
git add pixi.lock
git commit -m "Add pixi lock file"
git push
```

#### Issue: "Lock file is outdated"

**Error message:**
```
The pixi.lock file is outdated. Please run `pixi install` to update it.
```

**Cause:** You modified `pyproject.toml` without updating the lock file.

**Solution:**
```bash
# Update lock file
pixi install

# Commit both files
git add pyproject.toml pixi.lock
git commit -m "Update dependencies"
git push
```

#### Issue: Cache not working

**Symptoms:** Every run takes 5-10 minutes even with `cache: 'true'`

**Possible causes:**

1. **Lock file keeps changing:**
   ```bash
   # Check if lock file is in .gitignore
   git check-ignore pixi.lock
   # Should output nothing (not ignored)
   ```

2. **Running on PR from fork:**
   - Forks have limited cache access
   - This is a GitHub limitation

3. **Cache was cleared:**
   - Check GitHub Actions → Caches
   - Old caches are auto-deleted after 7 days

**Solution:**
- Ensure `pixi.lock` is committed
- Check cache hit/miss in logs
- For fork PRs, accept slower runs

#### Issue: "Environment not found"

**Error message:**
```
Error: Environment 'ml' not found
```

**Cause:** Trying to activate an environment that doesn't exist in `pyproject.toml` or wasn't installed.

**Solution:**
```yaml
# Wrong
with:
  environments: 'dev'
  activate-environment: 'ml'  # ❌ ml not installed!

# Correct
with:
  environments: 'dev ml'       # ✅ Install both
  activate-environment: 'ml'   # ✅ Now can activate ml
```

#### Issue: Package not found after setup

**Symptoms:** `ModuleNotFoundError: No module named 'numpy'` even though it's in `pyproject.toml`

**Possible causes:**

1. **Wrong environment activated:**
   ```yaml
   # Package is in 'ml' environment but 'dev' is active
   with:
     environments: 'dev ml'
     activate-environment: 'dev'  # numpy might not be here
   
   - run: python -c "import numpy"  # ❌ Fails
   ```

2. **Package in wrong feature:**
   Check your `pyproject.toml` environment definitions

**Solution:**
```bash
# Check which environment has the package
pixi list -e dev | grep numpy
pixi list -e ml | grep numpy

# Either switch environment or add package to current environment
```

#### Issue: Different versions locally vs CI

**Symptoms:** Works locally but fails in CI (or vice versa)

**Cause:** Lock file not synchronized

**Solution:**
```bash
# Regenerate lock file locally
rm pixi.lock
pixi install

# Commit and push
git add pixi.lock
git commit -m "Regenerate lock file"
git push
```

#### Issue: Windows-specific path issues

**Symptoms:** Works on Linux/Mac but fails on Windows

**Cause:** Path separators or shell-specific commands

**Solution:**
```yaml
# Use pixi tasks instead of shell commands
# In pyproject.toml:
[tool.pixi.tasks]
test = "pytest tests/"

# In workflow:
- run: pixi run test  # Cross-platform!
```

#### Issue: Slow installation even with cache

**Symptoms:** Cache hits but still takes 2-3 minutes

**Cause:** Lock verification and environment activation take time

**Solution:**
```yaml
# For trusted environments, disable verification
with:
  cache: 'true'
  verify-lock: 'false'  # Faster but less safe
```

### Debug Mode

To get more information about what's happening:

```yaml
- uses: serapeum-org/github-actions/actions/python-setup/pixi@v1
  with:
    cache: 'false'

# Add debug steps
- name: Debug environment info
  run: |
    echo "Pixi version:"
    pixi --version
    
    echo "Available environments:"
    pixi info
    
    echo "Active Python:"
    which python
    python --version
    
    echo "Installed packages:"
    pixi list
    
    echo "PATH:"
    echo $PATH
```

## Best Practices

### 1. Always Commit Lock Files

✅ **DO:**
```bash
git add pyproject.toml pixi.lock
git commit -m "Update numpy to 2.0"
```

❌ **DON'T:**
```bash
git add pyproject.toml
# Missing pixi.lock - CI will fail!
```

### 2. Use Locked Mode in CI

✅ **DO:**
```yaml
with:
  verify-lock: 'true'  # Catch drift
```

❌ **DON'T:**
```yaml
with:
  verify-lock: 'false'  # Silent failures
```

**Exception:** Disable when lock is auto-updated by bots

### 3. Enable Caching for Stable Projects

✅ **DO:**
```yaml
# Stable project with infrequent dependency changes
with:
  cache: 'true'
```

❌ **DON'T:**
```yaml
# When debugging dependency issues
with:
  cache: 'true'  # Cache might mask issues
```

### 4. Use Minimal Environments

✅ **DO:**
```yaml
# Install only what you need
jobs:
  lint:
    steps:
      - uses: .../pixi@v1
        with:
          environments: 'dev'  # Just linting tools

  test:
    steps:
      - uses: .../pixi@v1
        with:
          environments: 'test'  # Just test deps
```

❌ **DON'T:**
```yaml
# Install everything everywhere
jobs:
  lint:
    steps:
      - uses: .../pixi@v1
        with:
          environments: 'dev test ml viz'  # Overkill!
```

### 5. One Environment Activation Per Job

✅ **DO:**
```yaml
- uses: .../pixi@v1
  with:
    environments: 'dev'
    activate-environment: 'dev'

# All subsequent steps use dev environment
```

❌ **DON'T:**
```yaml
# Trying to activate multiple environments (not possible)
- uses: .../pixi@v1
  with:
    activate-environment: 'dev'

- uses: .../pixi@v1  # ❌ Second activation
  with:
    activate-environment: 'test'
```

**If you need multiple environments**, use `pixi run -e`:
```yaml
- uses: .../pixi@v1
  with:
    environments: 'dev test'
    activate-environment: 'dev'

- run: black --check .  # Uses dev

- run: pixi run -e test pytest  # Uses test
```

### 6. Organize Dependencies by Purpose

✅ **DO:**
```toml
[tool.pixi.feature.core.dependencies]
# Core runtime dependencies
numpy = ">=1.26"
pandas = ">=2.0"

[tool.pixi.feature.dev.dependencies]
# Development tools
black = ">=23.0"
ruff = ">=0.1"

[tool.pixi.feature.test.dependencies]
# Testing tools
pytest = ">=7.0"
pytest-cov = ">=4.0"

[tool.pixi.environments]
default = ["core"]
dev = ["core", "dev"]
ci = ["core", "test"]
```

❌ **DON'T:**
```toml
[tool.pixi.dependencies]
# Everything in one place
numpy = ">=1.26"
pandas = ">=2.0"
black = ">=23.0"
pytest = ">=7.0"
# No organization!
```

### 7. Use Descriptive Environment Names

✅ **DO:**
```toml
[tool.pixi.environments]
default = ["core"]
dev = ["core", "dev-tools"]
test-py311 = ["core", "test", "py311"]
test-py312 = ["core", "test", "py312"]
prod = ["core"]
```

❌ **DON'T:**
```toml
[tool.pixi.environments]
env1 = ["core"]
env2 = ["core", "dev"]
myenv = ["core", "test"]
```

### 8. Document Environment Purpose

✅ **DO:**
```toml
[tool.pixi.environments]
# Core dependencies only - minimal install
default = ["core"]

# Development environment - includes linting and formatting tools
dev = ["core", "dev-tools"]

# CI testing environment - includes test runners and coverage
ci = ["core", "test"]

# Production environment - runtime dependencies only
prod = ["core"]
```

### 9. Pin Major Python Version

✅ **DO:**
```toml
[tool.pixi.dependencies]
python = ">=3.11,<3.13"  # Explicit range
```

❌ **DON'T:**
```toml
[tool.pixi.dependencies]
python = ">=3.11"  # Too permissive
```

### 10. Test Lock File Verification in CI

✅ **DO:**
```yaml
jobs:
  validate-lock:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      
      - uses: .../pixi@v1
        with:
          verify-lock: 'true'  # Enforce verification
          cache: 'false'
```

This catches PRs with outdated lock files early.

## Migration Guide

### From `setup-python` + `pip`

**Before (pip):**
```yaml
- uses: actions/setup-python@v5
  with:
    python-version: '3.11'
    cache: 'pip'

- run: pip install -r requirements.txt
```

**After (pixi):**
```yaml
- uses: serapeum-org/github-actions/actions/python-setup/pixi@v1
  with:
    cache: 'true'
```

**Migration steps:**
1. Create `pyproject.toml` with pixi configuration
2. Run `pixi install` locally to generate `pixi.lock`
3. Commit both files
4. Update workflow to use pixi action

### From `setup-python` + `conda`

**Before (conda):**
```yaml
- uses: conda-incubator/setup-miniconda@v3
  with:
    python-version: '3.11'
    environment-file: environment.yml
```

**After (pixi):**
```yaml
- uses: serapeum-org/github-actions/actions/python-setup/pixi@v1
  with:
    cache: 'true'
```

**Migration steps:**
1. Convert `environment.yml` to `pyproject.toml` pixi format
2. Run `pixi install` to generate lock file
3. Commit files
4. Update workflow

### From `mamba-org/setup-micromamba`

**Before (micromamba):**
```yaml
- uses: mamba-org/setup-micromamba@v1
  with:
    environment-file: environment.yml
    cache-environment: true
```

**After (pixi):**
```yaml
- uses: serapeum-org/github-actions/actions/python-setup/pixi@v1
  with:
    cache: 'true'
```

Pixi is faster than micromamba and has better lock file support!

## Additional Resources

- **Pixi Documentation**: https://prefix.dev/docs/pixi
- **Pixi GitHub**: https://github.com/prefix-dev/pixi
- **Conda-forge**: https://conda-forge.org/
- **Action Source**: `serapeum-org/github-actions/actions/python-setup/pixi`

## Examples Repository

See the test suite for comprehensive examples:
- `.github/workflows/test-python-setup-pixi.yml` - All test scenarios
- `tests/data/pixi/` - Example configurations

## Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting)
2. Review [test examples](.github/workflows/test-python-setup-pixi.yml)
3. Open an issue in the repository

---

**Version**: 1.0.0  
**Last Updated**: January 2026  
**Compatibility**: Linux, macOS, Windows  
**Pixi Version**: v0.49.0

