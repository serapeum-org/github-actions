# Getting Started

This guide walks you through using the Serapeum GitHub Actions in your Python project.

## Prerequisites

- A GitHub repository with a Python project
- A `pyproject.toml` file (recommended) or `requirements.txt`

## Step 1: Choose a Package Manager

| Manager | Best For | Lock File |
|---------|----------|-----------|
| **uv** | Speed, modern projects, PEP 735 | `uv.lock` |
| **pip** | Compatibility, simple projects | None (uses `pyproject.toml`) |
| **pixi** | Conda ecosystem, multi-environment | `pixi.lock` |

!!! tip "Recommendation"
    Use **uv** for new projects. It's the fastest and has full PEP 735 dependency group support.

## Step 2: Set Up Python Environment

Add a workflow file at `.github/workflows/ci.yml`:

=== "uv"

    ```yaml
    name: CI

    on: [push, pull_request]

    jobs:
      test:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v5

          - uses: serapeum-org/github-actions/actions/python-setup/uv@uv/v1
            with:
              python-version: '3.12'
              install-groups: 'groups: dev test'

          - run: pytest
    ```

=== "pip"

    ```yaml
    name: CI

    on: [push, pull_request]

    jobs:
      test:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v5

          - uses: serapeum-org/github-actions/actions/python-setup/pip@pip/v1
            with:
              python-version: '3.12'
              cache: 'pip'
              install-groups: 'extras: dev test'

          - run: pytest
    ```

=== "pixi"

    ```yaml
    name: CI

    on: [push, pull_request]

    jobs:
      test:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v5

          - uses: serapeum-org/github-actions/actions/python-setup/pixi@pixi/v1
            with:
              environments: 'default'

          - run: pixi run pytest
    ```

## Step 3: Add Documentation Deployment (Optional)

Deploy MkDocs to GitHub Pages with automatic versioning:

```yaml
name: Docs

on:
  push:
    branches: [main]
  pull_request:
  release:
    types: [published]

jobs:
  docs:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v5
        with:
          fetch-depth: 0

      - uses: serapeum-org/github-actions/actions/mkdocs-deploy@mkdocs-deploy/v1
        with:
          trigger: ${{ github.event_name }}
          deploy-token: ${{ secrets.GITHUB_TOKEN }}
          package-manager: 'uv'
          install-groups: 'groups: docs'
```

## Step 4: Automate Releases (Optional)

### GitHub Releases

```yaml
name: Release

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
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
        with:
          fetch-depth: 0

      - uses: serapeum-org/github-actions/actions/release/github@release-github/v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          increment: ${{ inputs.increment }}
```

### PyPI Publishing

```yaml
name: Publish

on:
  release:
    types: [published]

permissions:
  id-token: write

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5

      - uses: serapeum-org/github-actions/actions/release/pypi@release-pypi/v1
        with:
          pypi-username: '__token__'
          pypi-password: ${{ secrets.PYPI_TOKEN }}
```

## Step 5: Add Matrix Testing

Test across multiple Python versions and operating systems:

```yaml
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.11', '3.12', '3.13']
    steps:
      - uses: actions/checkout@v5

      - uses: serapeum-org/github-actions/actions/python-setup/uv@uv/v1
        with:
          python-version: ${{ matrix.python-version }}
          install-groups: 'groups: test'

      - run: pytest
```

## Dependency Groups Format

The `install-groups` input supports a flexible format:

| Format | Example | Result |
|--------|---------|--------|
| Dependency groups (PEP 735) | `'groups: dev test'` | Installs `[dependency-groups]` entries |
| Optional dependencies | `'extras: aws viz'` | Installs `[project.optional-dependencies]` entries |
| Both combined | `'groups: dev, extras: aws'` | Installs both |
| Empty (default) | `''` | Core dependencies only |

!!! note
    For **pixi**, the `install-groups` input is replaced by `environments` which takes pixi environment names.

## Next Steps

- Browse the [Actions Reference](reference/index.md) for complete input/output tables
- Read the individual action guides for detailed usage scenarios
- See the [Versioning Guide](VERSIONING.md) for release tag conventions
