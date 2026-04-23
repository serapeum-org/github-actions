# Deploy MkDocs

> Deploy MkDocs documentation to GitHub Pages with versioning support

## Usage

```yaml
- uses: serapeum-org/github-actions/actions/mkdocs-deploy@mkdocs/v1
  with:
    trigger: # required
    package-manager: 'uv'
    python-version: '3.12'
    install-groups: 'groups: docs'
    deploy-token: # required
    release-tag: ''
    mike-alias: 'latest'
    notebooks-path: ''
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|:--------:|---------|
| `trigger` | Deployment trigger type (pull_request, main, release) | Yes | - |
| `package-manager` | Package manager to use (pip, uv, pixi) | No | `uv` |
| `python-version` | Python version to install | No | `3.12` |
| `install-groups` | Dependency groups to install | No | `groups: docs` |
| `deploy-token` | GitHub token for deployment | Yes | - |
| `release-tag` | Release tag version (for release trigger) | No | - |
| `mike-alias` | Mike alias for releases (e.g., latest) | No | `latest` |
| `notebooks-path` | Root directory of Jupyter notebooks to execute and cache before the mkdocs build. Requires `jupyter`, `nbconvert`, `ipykernel`, `mkdocs-jupyter` in `install-groups`, and a src-layout project (`src/**/*.py`, `pyproject.toml` at root). Empty = skip. See [mkdocs-deploy guide](../mkdocs-deploy.md#notebook-execution). | No | `''` (skip) |
