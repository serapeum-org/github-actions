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

## How It Works

1. Sets up Python environment using the selected package manager action
2. Configures git with the workflow actor's identity
3. Runs the appropriate `mike` command based on trigger:
   - **pull_request**: `mike deploy --push develop`
   - **main**: `mike deploy --push --update-aliases main latest && mike set-default --push latest`
   - **release**: `mike deploy --push --update-aliases <tag> latest`
4. For non-pip managers, commands are prefixed with `<manager> run`

## Prerequisites

- `mkdocs` and `mike` in your project dependencies
- GitHub Pages enabled on the repository
- `contents: write` permission in the workflow
