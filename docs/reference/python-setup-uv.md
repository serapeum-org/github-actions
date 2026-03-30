# Setup Python with uv

> Setup Python environment with uv package manager and install dependencies

## Usage

```yaml
- uses: serapeum-org/github-actions/actions/python-setup/uv@uv/v1
  with:
    python-version: '3.12'
    cache: 'true'
    install-groups: ''
    verify-lock: 'true'
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|:--------:|---------|
| `python-version` | Python version to install, default is 3.12 | No | `3.12` |
| `cache` | Enable caching of uv dependencies | No | `true` |
| `install-groups` | examples: "groups: dev test, extras: aws viz" or "groups: dev" or "extras: aws viz" | No | - |
| `verify-lock` | Whether to verify the lock file is up to date | No | `true` |
