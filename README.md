# Serapeum GitHub Actions

[![Test pip](https://github.com/serapeum-org/github-actions/actions/workflows/test-python-setup-pip.yml/badge.svg)](https://github.com/serapeum-org/github-actions/actions/workflows/test-python-setup-pip.yml)
[![Test uv](https://github.com/serapeum-org/github-actions/actions/workflows/test-python-setup-uv.yml/badge.svg)](https://github.com/serapeum-org/github-actions/actions/workflows/test-python-setup-uv.yml)
[![Test pixi](https://github.com/serapeum-org/github-actions/actions/workflows/test-python-setup-pixi.yml/badge.svg)](https://github.com/serapeum-org/github-actions/actions/workflows/test-python-setup-pixi.yml)
[![Test mkdocs-deploy](https://github.com/serapeum-org/github-actions/actions/workflows/test-mkdocs-deploy.yml/badge.svg)](https://github.com/serapeum-org/github-actions/actions/workflows/test-mkdocs-deploy.yml)
[![Test release-github](https://github.com/serapeum-org/github-actions/actions/workflows/test-release-github.yml/badge.svg)](https://github.com/serapeum-org/github-actions/actions/workflows/test-release-github.yml)
[![Test release-pypi](https://github.com/serapeum-org/github-actions/actions/workflows/test-release-pypi.yml/badge.svg)](https://github.com/serapeum-org/github-actions/actions/workflows/test-release-pypi.yml)

Reusable composite GitHub Actions for Python CI/CD workflows. Cross-platform
(Windows, macOS, Linux), supporting pip, uv, and pixi package managers.

**📚 Full documentation: <https://serapeum-org.github.io/github-actions/>**

The docs site (built with MkDocs + mike versioning, deployed from this repo)
covers every action in depth — inputs, outputs, examples, and the consumer
contract for each. This README is a top-level index.

## Actions

### Python Setup

Set up Python with your preferred package manager, install dependencies,
and configure caching. All three share the same `install-groups` input shape
(PEP 735 groups and/or extras) and lock-file verification defaults.

| Action | Usage | Guide | Reference |
|---|---|---|---|
| **pip** | `serapeum-org/github-actions/actions/python-setup/pip@pip/v1` | [guide](docs/python-setup/pip.md) | [reference](docs/reference/python-setup-pip.md) |
| **uv** | `serapeum-org/github-actions/actions/python-setup/uv@uv/v1` | [guide](docs/python-setup/uv.md) | [reference](docs/reference/python-setup-uv.md) |
| **pixi** | `serapeum-org/github-actions/actions/python-setup/pixi@pixi/v1` | [guide](docs/python-setup/pixi.md) | [reference](docs/reference/python-setup-pixi.md) |

### Documentation

| Action | Usage | Guide | Reference |
|---|---|---|---|
| **mkdocs-deploy** | `serapeum-org/github-actions/actions/mkdocs-deploy@mkdocs/v1` | [guide](docs/mkdocs-deploy.md) | [reference](docs/reference/mkdocs-deploy.md) |

`mkdocs-deploy` builds and publishes a versioned MkDocs site to GitHub Pages
via [mike](https://github.com/jimporter/mike). Version deployed is selected
by the `trigger` input — `pull_request` → `develop`, `main` → `main`
(default), `release` → the tagged version (with a configurable alias, e.g.
`latest`).

**New in `mkdocs/v1.1.0`** — opt-in Jupyter notebook execution with caching.
Set `notebooks-path: 'docs/notebook'` and the action will walk your notebook
tree, restore `.jupyter_cache/` from `actions/cache` (keyed on notebook
contents + `src/**/*.py` + `pyproject.toml`), preflight that
`jupyter`/`nbconvert`/`ipykernel` are importable, execute uncached notebooks
via `jupyter nbconvert --execute`, and feed the populated outputs into
mkdocs-jupyter (which runs with `execute: false`). Omitting `notebooks-path`
(the default) skips notebook execution entirely — zero behaviour change for
existing consumers. See the [notebook-execution
section](docs/mkdocs-deploy.md#notebook-execution) of the guide for the
consumer contract (required deps, mkdocs-jupyter config, src-layout
assumption, concrete `pyproject.toml` snippet).

### Release

| Action | Usage | Guide | Examples |
|---|---|---|---|
| **GitHub Release** | `serapeum-org/github-actions/actions/release/github@github-release/v1` | [guide](docs/release/github/README.md) | [examples](docs/release/github/EXAMPLES.md) |
| **PyPI Release** | `serapeum-org/github-actions/actions/release/pypi@pypi-release/v1` | [guide](docs/release/pypi/README.md) | [examples](docs/release/pypi/EXAMPLES.md) |

The `release/github` action automates version bumping via
[Commitizen](https://commitizen-tools.github.io/commitizen/), writes the
changelog incrementally from the source of truth, creates a git tag, and
publishes a GitHub Release whose body is extracted directly from the
changelog (so release notes and project changelog stay in sync).

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

Deploy docs (with notebook execution) on every PR, main push, and release:

```yaml
- uses: serapeum-org/github-actions/actions/mkdocs-deploy@mkdocs/v1
  with:
    trigger: ${{ github.event_name }}
    deploy-token: ${{ secrets.GITHUB_TOKEN }}
    notebooks-path: 'docs/notebook'
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
pip/v1.0.0      pip/v1       # Python setup with pip
uv/v1.2.0       uv/v1        # Python setup with uv
pixi/v1.0.0     pixi/v1      # Python setup with pixi
mkdocs/v1.1.0   mkdocs/v1    # MkDocs deploy (notebook execution in v1.1.0)
github-release/v1.0.0        github-release/v1
pypi-release/v1.0.0          pypi-release/v1
```

Pin to a major-version tag for automatic patch/minor updates, pin to an
exact patch for reproducibility, or pin to a commit SHA for supply-chain
hardening:

```yaml
# Auto-update within v1 (recommended for most consumers)
uses: serapeum-org/github-actions/actions/python-setup/uv@uv/v1

# Exact patch (for reproducibility)
uses: serapeum-org/github-actions/actions/python-setup/uv@uv/v1.2.0

# Commit SHA (immutable — survives tag retagging)
uses: serapeum-org/github-actions/actions/python-setup/uv@65da263cc0f804cba87da3cbe6024d528831be1d  # uv/v1
```

### Current rolling-`v1` commit SHAs

For SHA-based pinning, here is the commit each `…/v1` tag resolves to today.
Update these when you bump a `v1` rolling tag.

| Action | Rolling tag | Commit SHA |
|---|---|---|
| `actions/python-setup/pip` | `pip/v1` | `65da263cc0f804cba87da3cbe6024d528831be1d` |
| `actions/python-setup/uv` | `uv/v1` | `65da263cc0f804cba87da3cbe6024d528831be1d` |
| `actions/python-setup/pixi` | `pixi/v1` | `65da263cc0f804cba87da3cbe6024d528831be1d` |
| `actions/mkdocs-deploy` | `mkdocs/v1` | `f861b115f7ac3c68629f9adbd40d9edd406d2a74` |
| `actions/release/github` | `github-release/v1` | `6823246a90df2963d1576ef6de875e10467c64aa` |
| `actions/release/pypi` | `pypi-release/v1` | `65da263cc0f804cba87da3cbe6024d528831be1d` |

To verify locally: `git rev-parse <tag>^{commit}` (the `^{commit}` is
required — `git rev-parse <tag>` returns the annotated-tag object SHA, not
the commit it points at).

See the [Versioning Guide](docs/VERSIONING.md) for release workflow, tag
conventions, and breaking-change policy.

## Documentation

- **Hosted docs**: <https://serapeum-org.github.io/github-actions/> (MkDocs,
  versioned via mike — includes `latest`, `main`, and per-release tags).
- **In-repo guides**: under `docs/` — same content as the hosted site.
- **Action reference pages**: auto-generated from each `action.yml` into
  `docs/reference/` by `scripts/generate_action_docs.py` (runs in CI on every
  push to `main` that changes an action).
- **Getting Started**: [docs/getting-started.md](docs/getting-started.md).

## Contributing

1. Read the test workflows in `.github/workflows/test-*.yml` to understand
   how each action is exercised.
2. Use test fixtures under `tests/data/` — never hand-roll inline fixtures.
3. Maintain cross-platform compatibility (`shell: bash`, forward-slash paths,
   string-typed booleans).
4. Every test job that invokes an action whose code path can reach
   `git push`, `mike deploy`, `gh release create`, or PyPI upload MUST call
   `./.github/workflows/test-helpers/setup-fake-remote` between `actions/checkout`
   and the first action invocation — pushes must never escape to the real
   GitHub repo.
5. Follow [semantic versioning](docs/VERSIONING.md): new optional input =
   MINOR; behaviour-preserving fix or docs = PATCH; removed/renamed input or
   changed default behaviour = MAJOR.

## License

See [LICENSE](LICENSE) for details.
