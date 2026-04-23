# Serapeum GitHub Actions

[![Test pip](https://github.com/serapeum-org/github-actions/actions/workflows/test-python-setup-pip.yml/badge.svg)](https://github.com/serapeum-org/github-actions/actions/workflows/test-python-setup-pip.yml)
[![Test uv](https://github.com/serapeum-org/github-actions/actions/workflows/test-python-setup-uv.yml/badge.svg)](https://github.com/serapeum-org/github-actions/actions/workflows/test-python-setup-uv.yml)
[![Test pixi](https://github.com/serapeum-org/github-actions/actions/workflows/test-python-setup-pixi.yml/badge.svg)](https://github.com/serapeum-org/github-actions/actions/workflows/test-python-setup-pixi.yml)

Reusable composite GitHub Actions for Python CI/CD workflows. Cross-platform (Windows, macOS, Linux), supporting pip, uv, and pixi package managers.

## Actions

### Python Setup

Set up Python with your preferred package manager, install dependencies, and configure caching.

| Action | Usage |
|--------|-------|
| **[pip](docs/python-setup/pip.md)** | `serapeum-org/github-actions/actions/python-setup/pip@pip/v1` |
| **[uv](docs/python-setup/uv.md)** | `serapeum-org/github-actions/actions/python-setup/uv@uv/v1` |
| **[pixi](docs/python-setup/pixi.md)** | `serapeum-org/github-actions/actions/python-setup/pixi@pixi/v1` |

### Documentation

| Action | Usage |
|--------|-------|
| **[mkdocs-deploy](docs/mkdocs-deploy.md)** | `serapeum-org/github-actions/actions/mkdocs-deploy@mkdocs/v1` |

### Release

| Action | Usage |
|--------|-------|
| **[GitHub Release](docs/release/github/README.md)** | `serapeum-org/github-actions/actions/release/github@release-github/v1` |
| **[PyPI Release](docs/release/pypi/README.md)** | `serapeum-org/github-actions/actions/release/pypi@release-pypi/v1` |

## Quick Start

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

## Dependency Groups Format

The `install-groups` input (for pip and uv) supports:

```yaml
# PEP 735 dependency groups
install-groups: 'groups: dev test'

# Optional dependencies (extras)
install-groups: 'extras: aws viz'

# Both combined
install-groups: 'groups: dev, extras: aws'
```

For pixi, use the `environments` input instead:

```yaml
environments: 'default py312'
```

## Versioning

Each action is versioned independently with namespaced tags:

```
pip/v1.0.0     pip/v1       # Python setup with pip
uv/v1.2.0      uv/v1        # Python setup with uv
pixi/v1.0.0    pixi/v1      # Python setup with pixi
```

Pin to a major version tag for automatic patch/minor updates:

```yaml
uses: serapeum-org/github-actions/actions/python-setup/uv@uv/v1
```

See the [Versioning Guide](docs/VERSIONING.md) for details.

## Documentation

Full documentation is available at the [docs site](https://serapeum-org.github.io/github-actions/) or browse the `docs/` directory.

## Contributing

1. Read the test workflows in `.github/workflows/test-*.yml`
2. Use test fixtures from `tests/data/`
3. Maintain cross-platform compatibility (`shell: bash`)
4. Follow [semantic versioning](docs/VERSIONING.md)

## License

See [LICENSE](LICENSE) for details.
