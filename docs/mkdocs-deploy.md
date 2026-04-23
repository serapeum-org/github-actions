# MkDocs Deploy Action

> Deploy MkDocs documentation to GitHub Pages with versioning support using [mike](https://github.com/jimporter/mike).

## Overview

This action deploys MkDocs documentation with automatic version management based on the trigger event:

| Trigger | Version Deployed | Alias |
|---------|-----------------|-------|
| `pull_request` | `develop` | - |
| Push to `main` | `main` | `latest` (default) |
| `release` | Tag version (e.g. `v1.2.0`) | Configurable (default: `latest`) |

## Usage

```yaml
- uses: serapeum-org/github-actions/actions/mkdocs-deploy@mkdocs-deploy/v1
  with:
    trigger: ${{ github.event_name }}
    deploy-token: ${{ secrets.GITHUB_TOKEN }}
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|:--------:|---------|
| `trigger` | Deployment trigger type: `pull_request`, `main`, `release` | Yes | - |
| `package-manager` | Package manager: `pip`, `uv`, `pixi` | No | `uv` |
| `python-version` | Python version to install | No | `3.12` |
| `install-groups` | Dependency groups to install | No | `groups: docs` |
| `deploy-token` | GitHub token for deployment | Yes | - |
| `release-tag` | Release tag version (for release trigger) | No | - |
| `mike-alias` | Mike alias for releases | No | `latest` |
| `notebooks-path` | Root directory of Jupyter notebooks to execute and cache. Empty = skip. | No | `` (skip) |

## Examples

### Pull Request Preview

Deploy a `develop` version on every PR for review:

```yaml
name: Docs Preview

on: pull_request

permissions:
  contents: write

jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
        with:
          fetch-depth: 0

      - uses: serapeum-org/github-actions/actions/mkdocs-deploy@mkdocs-deploy/v1
        with:
          trigger: 'pull_request'
          deploy-token: ${{ secrets.GITHUB_TOKEN }}
```

### Production Deployment

Deploy on push to main and on release:

```yaml
name: Deploy Docs

on:
  push:
    branches: [main]
  release:
    types: [published]

permissions:
  contents: write

jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
        with:
          fetch-depth: 0

      - uses: serapeum-org/github-actions/actions/mkdocs-deploy@mkdocs-deploy/v1
        with:
          trigger: ${{ github.event_name == 'release' && 'release' || 'main' }}
          deploy-token: ${{ secrets.GITHUB_TOKEN }}
          release-tag: ${{ github.event.release.tag_name }}
```

### With pixi

```yaml
- uses: serapeum-org/github-actions/actions/mkdocs-deploy@mkdocs-deploy/v1
  with:
    trigger: 'main'
    deploy-token: ${{ secrets.GITHUB_TOKEN }}
    package-manager: 'pixi'
    install-groups: 'default'
```

### With notebook execution

Deploy docs that include executable Jupyter notebooks. The action runs
notebooks once, caches their outputs, and reuses the cache on subsequent runs
so unchanged notebooks don't re-execute:

```yaml
- uses: serapeum-org/github-actions/actions/mkdocs-deploy@mkdocs-deploy/v1
  with:
    trigger: ${{ github.event_name }}
    deploy-token: ${{ secrets.GITHUB_TOKEN }}
    notebooks-path: 'docs/notebook'
```

See [Notebook execution](#notebook-execution) below for the consumer contract.

## Notebook execution

Setting `notebooks-path` enables a pre-build step that executes Jupyter
notebooks and persists their outputs via `actions/cache`, so `mkdocs-jupyter`
can render them without re-executing on every CI run. Omitting
`notebooks-path` (the default) skips notebook execution entirely — existing
workflows see no change.

### Requirements

- **Dependencies**: four packages must be in the dependency group passed via
  `install-groups`, split by role:
    - `jupyter`, `nbconvert`, `ipykernel` — used by the action's notebook
      execution step. The action runs a preflight import check against
      these three and fails fast with an actionable error if any are
      missing.
    - `mkdocs-jupyter` — used later by the mkdocs build itself to render
      notebooks. A missing `mkdocs-jupyter` passes preflight but fails at
      build time with an mkdocs plugin error — so add it alongside the
      other three.

  Concrete example (statista's layout; adapt the group name to whatever you
  pass via `install-groups`):

  ```toml
  # pyproject.toml
  [dependency-groups]
  docs = [
      "mkdocs>=1.5",
      "mkdocs-material",
      "mkdocs-jupyter",   # rendering (mkdocs build)
      "mike",
      "jupyter",          # preflighted; drives nbconvert --execute
      "nbconvert",
      "ipykernel",
  ]
  ```
- **mkdocs-jupyter config**: set `execute: false` in `mkdocs.yml` so the
  plugin reads pre-executed outputs instead of re-running notebooks during
  the mkdocs build:
  ```yaml
  plugins:
    - mkdocs-jupyter:
        execute: false
  ```
- **Project layout**: `pyproject.toml` at repo root and library source under
  `src/`. The cache-invalidation hash covers notebook contents,
  `src/**/*.py`, and `pyproject.toml`; flat-layout projects (library code at
  repo root rather than under `src/`) are not supported out of the box.

### Cache invalidation

The cache key is:

```
jupyter-cache-<hashFiles(notebooks, src/**/*.py, pyproject.toml)>
```

Any change to a notebook, to library source under `src/`, or to
`pyproject.toml` invalidates the cache and triggers a full re-execute.
There is no `restore-keys` fallback — primary-key-only, so rendered outputs
always reflect the exact code that produced them.

### Stripping notebook outputs on commit

Because executed outputs are produced in CI, commit notebooks with their
outputs stripped. A `pre-commit` hook such as
[`nbstripout`](https://github.com/kynan/nbstripout) is the usual way.

## How It Works

1. Sets up Python environment using the selected package manager action
2. *(If `notebooks-path` is set)* Restores `.jupyter_cache/` from
   `actions/cache`, preflight-checks that `jupyter`/`nbconvert`/`ipykernel`
   are importable, and runs the vendored `prep_notebooks.py` script — which
   copies cached executed notebooks back into the working tree where
   available, and executes (via `jupyter nbconvert --execute --inplace`) the
   rest
3. Configures git with the workflow actor's identity
4. Runs the appropriate `mike` command based on trigger:
   - **pull_request**: `mike deploy --push develop`
   - **main**: `mike deploy --push --update-aliases main latest && mike set-default --push latest`
   - **release**: `mike deploy --push --update-aliases <tag> latest`
5. For non-pip managers, commands are prefixed with `<manager> run`

## Prerequisites

- `mkdocs` and `mike` in your project dependencies
- GitHub Pages enabled on the repository
- `contents: write` permission in the workflow
- *(For notebook execution)* `jupyter`, `nbconvert`, `ipykernel`,
  `mkdocs-jupyter` in the dependency group passed via `install-groups`;
  src-layout project structure
