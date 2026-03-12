# Setup Python with pip

> Setup Python environment with pip package manager for pyproject.toml projects

## Usage

```yaml
- uses: Serapieum-of-alex/github-actions/actions/python-setup/pip@pip/v1
  with:
    python-version: '3.12'
    cache: ''
    install-groups: ''
    architecture: 'x64'
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|:--------:|---------|
| `python-version` | Python version to install, default is 3.12 | No | `3.12` |
| `cache` | Cache packages dependencies (pip, pipenv, poetry), if empty no caching is performed, default is empty | No | - |
| `install-groups` | examples: "groups: dev test, extras: aws viz" or "groups: dev" or "extras: aws viz" | No | - |
| `architecture` | Target architecture for Python to use (x64, x86), default is x64 | No | `x64` |
