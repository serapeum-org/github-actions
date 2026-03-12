# Deploy MkDocs

> Deploy MkDocs documentation to GitHub Pages with versioning support

## Usage

```yaml
- uses: Serapieum-of-alex/github-actions/actions/mkdocs-deploy@mkdocs-deploy/v1
  with:
    trigger: # required
    package-manager: 'uv'
    python-version: '3.12'
    install-groups: 'groups: docs'
    deploy-token: # required
    release-tag: ''
    mike-alias: 'latest'
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
