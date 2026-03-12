# Setup Python with pixi

> Setup Python environment with pixi package manager and install dependencies

## Usage

```yaml
- uses: Serapieum-of-alex/github-actions/actions/python-setup/pixi@pixi/v1
  with:
    environments: 'default'
    activate-environment: 'default'
    cache: 'false'
    verify-lock: 'true'
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|:--------:|---------|
| `environments` | Pixi environments to install (e.g., "py311", "py312 py313") | No | `default` |
| `activate-environment` | Environment to activate after installation | No | `default` |
| `cache` | Whether to enable caching of pixi environments | No | `false` |
| `verify-lock` | Whether to verify the lock file is up to date | No | `true` |
