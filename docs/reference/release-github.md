# GitHub Release

> Create a GitHub release with optional package manager setup for building/testing

## Usage

```yaml
- uses: serapeum-org/github-actions/actions/release/github@github-release/v1
  with:
    github-token: # required
    increment: 'patch'
    prerelease-type: 'none'
    draft: 'false'
    package-manager: 'uv'
    python-version: '3.12'
    install-groups: 'groups: docs dev'
    config-file: ''
    skip-github-release: 'false'
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|:--------:|---------|
| `github-token` | GitHub token for creating releases | Yes | - |
| `increment` | Version increment type used by commitizen for semantic versioning | No | `patch` |
| `prerelease-type` | Prerelease type appended to the version (used with commitizen --prerelease flag) | No | `none` |
| `draft` | Create as draft release (passed to softprops/action-gh-release) | No | `false` |
| `package-manager` | Package manager to use for setting up Python environment before release | No | `uv` |
| `python-version` | Python version to install (passed to actions/setup-python) | No | `3.12` |
| `install-groups` | Dependency groups or environments to install | No | `groups: docs dev` |
| `config-file` | Path to a commitizen configuration file (pyproject.toml) | No | - |
| `skip-github-release` | Skip creating the GitHub release via API | No | `false` |
