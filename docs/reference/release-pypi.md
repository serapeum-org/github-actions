# PyPI Release

> Build and publish a Python package to PyPI using twine

## Usage

```yaml
- uses: serapeum-org/github-actions/actions/release/pypi@pypi-release/v1
  with:
    pypi-username: # required
    pypi-password: # required
    python-version: '3.12'
    package-manager: 'uv'
    install-groups: ''
    pypi-repository-url: ''
    verify-lock: 'true'
    package: ''
    skip-publish: 'false'
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|:--------:|---------|
| `pypi-username` | PyPI username | Yes | - |
| `pypi-password` | PyPI password or API token | Yes | - |
| `python-version` | Python version to use for building and publishing | No | `3.12` |
| `package-manager` | Package manager to use for setting up the Python environment | No | `uv` |
| `install-groups` | Dependency groups or environments to install | No | - |
| `pypi-repository-url` | PyPI repository URL | No | - |
| `verify-lock` | Whether to verify the lock file is up to date before installing (uv and pixi only) | No | `true` |
| `package` | Workspace package name to build | No | - |
| `skip-publish` | Skip the publish step | No | `false` |
