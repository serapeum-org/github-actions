# GitHub Release Action

Automate version bumping and GitHub release creation using Commitizen with support for multiple Python package managers.

## Overview

This composite action streamlines the release process by:

- **Automatically bumping versions** using Commitizen based on conventional commits
- **Generating/updating CHANGELOG.md** (full or incremental)
- **Creating git tags** with semantic versioning
- **Publishing GitHub releases** with auto-generated release notes
- **Supporting multiple package managers**: pip, uv, pixi

## Quick Start

### Basic Usage

```yaml
name: Release

on:
  workflow_dispatch:
    inputs:
      increment:
        description: 'Version increment type'
        required: true
        type: choice
        options:
          - patch
          - minor
          - major
        default: 'patch'

permissions:
  contents: write

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - name: Create GitHub Release
        uses: serapeum-org/github-actions/actions/release/github@github-release/v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          increment: ${{ inputs.increment }}
```

### With Custom Configuration

```yaml
- name: Create GitHub Release
  uses: serapeum-org/github-actions/actions/release/github@github-release/v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    release-branch: 'main'
    increment: 'minor'
    prerelease-type: 'beta'
    draft: 'false'
    package-manager: 'uv'
    python-version: '3.12'
    install-groups: 'groups: dev docs'
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `github-token` | GitHub token for creating releases (use `secrets.GITHUB_TOKEN`) | ✅ Yes | - |
| `release-branch` | Branch to create release from | No | `main` |
| `increment` | Version increment: `patch`, `minor`, `major` | No | `patch` |
| `prerelease-type` | Prerelease type: `none`, `alpha`, `beta`, `rc` | No | `none` |
| `draft` | Create as draft release (`true`/`false`) | No | `false` |
| `package-manager` | Package manager: `pip`, `uv`, `pixi` | No | `uv` |
| `package-manager-version` | Version of the `uv`/`pixi` package manager (forwarded to its `version` input); ignored for `pip`. | No | `latest` |
| `python-version` | Python version to install | No | `3.12` |
| `install-groups` | Dependency groups to install (see below) — **required, no default**; must include the group that provides commitizen | Yes | _(none)_ |
| `config-file` | Path to a per-package `pyproject.toml` (monorepo use) | No | `''` (root) |
| `skip-github-release` | Skip GitHub Releases API call (testing only) | No | `false` |

### Install Groups Format

The `install-groups` input format varies by package manager:

**For pip/uv:**
- `"groups: dev test"` - Install dependency groups (PEP 735)
- `"extras: aws viz"` - Install optional dependencies
- `"groups: dev, extras: aws"` - Combine both
- `""` - Install only core dependencies

**For pixi:**
- `"default"` - Use default environment
- `"py312"` - Single named environment
- `"py312 py313"` - Multiple environments

## Monorepo Support

Use the `config-file` input to release a sub-package in a monorepo that has its own Commitizen configuration.

```yaml
- name: Release sub-package
  uses: serapeum-org/github-actions/actions/release/github@github-release/v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    increment: 'minor'
    config-file: 'libs/my-package/pyproject.toml'
```

### How it works

When `config-file` is provided, the action determines the working directory as `dirname(config-file)` (e.g. `libs/my-package/`) and runs all Commitizen commands from there. The Python environment is still installed from the repository root before changing directory.

**Important:** All paths inside the sub-package's `pyproject.toml` Commitizen config must be relative to that sub-package directory, **not** the repository root:

```toml
# libs/my-package/pyproject.toml
[tool.commitizen]
name = "cz_conventional_commits"
version = "0.1.0"
version_files = ["pyproject.toml:version"]   # relative to libs/my-package/
tag_format = "my-package-$version"
update_changelog_on_bump = true
changelog_file = "docs/change-log.md"        # relative to libs/my-package/
```

The root `pyproject.toml` and its changelog are left untouched.

## Prerequisites

### Required Files

1. **pyproject.toml** with Commitizen configuration:

```toml
[tool.commitizen]
name = "cz_conventional_commits"
version = "0.1.0"
version_files = ["pyproject.toml:version"]
tag_format = "$version"
update_changelog_on_bump = true  # Required for automatic changelog updates
```

**Important:** The `update_changelog_on_bump = true` setting is **recommended** but not strictly required. If not set, the action will detect this and generate the changelog manually, then amend it to the version bump commit.

**Optional Commitizen settings:**

```toml
[tool.commitizen]
# ... other settings ...
changelog_file = "CHANGELOG.md"      # Custom changelog path (default: CHANGELOG.md)
changelog_incremental = true         # Incremental updates (default: false)
changelog_merge_prerelease = true    # Merge prerelease entries (default: false)
```

2. **Changelog file** (default: `CHANGELOG.md`, can be empty initially):

```markdown
# Changelog

All notable changes to this project will be documented in this file.
```

### Commitizen in Dependencies

Add Commitizen to your project dependencies:

```toml
[dependency-groups]
dev = [
    "commitizen>=3.0.0",
]
```

### Changelog settings: first release vs. subsequent releases

Two Commitizen settings interact with how this action generates the changelog, and the correct values differ for the
very first release (no git tags yet) versus every release after it.

- `changelog_incremental` — when `true`, Commitizen only appends the new version's section by diffing against the
  **previous tag**. A first release has no previous tag, so `cz changelog` fails with
  `No tag found to do an incremental changelog` (exit code 16) and the release aborts.
- `update_changelog_on_bump` — when `true`, `cz bump` updates the changelog as part of the version bump. On a
  non-first release this is the **only** thing that advances the changelog (the action does not run a separate
  changelog step once tags exist). `changelog_incremental` has no effect unless this is `true`.

**For the first release** (no tags yet):

```toml
[tool.commitizen]
changelog_incremental    = false   # true -> "No tag found to do an incremental changelog" (exit 16)
update_changelog_on_bump = true    # first release still works: the action generates the changelog itself
```

The action detects the first release, generates the full changelog with `cz changelog`, and (if
`update_changelog_on_bump = true`) temporarily toggles it off for the bump, then restores it — so you can set
`update_changelog_on_bump = true` from the start and never touch it again.

**For every release after the first** (a tag now exists):

```toml
[tool.commitizen]
changelog_incremental    = true    # safe now — a prior tag exists; appends only the new section
update_changelog_on_bump = true    # required, or the changelog stops advancing past the last release
```

`changelog_incremental = true` is optional — `false` keeps working and just regenerates the whole changelog from
history each run (more diff churn, identical content). `update_changelog_on_bump = true` is the one that matters: if
it is `false`, releases after the first bump the version and tag but never update the changelog, and the GitHub
Release notes fall back to a generic `Release X`.

**Simplest set-once config** (works for the first release and all later ones, no flag juggling):

```toml
[tool.commitizen]
changelog_incremental    = false
update_changelog_on_bump = true
```

> Merge the release branch into the default branch with a **merge commit or fast-forward, never a squash or rebase**.
> Squash/rebase rewrite the commit the tag points at, leaving the version tag unreachable from the default branch,
> which breaks `git describe` and the next release's incremental changelog range.

## How It Works

### Release Flow

1. **Prerequisites Check**
   - Validates CHANGELOG.md exists
   - Checks for existing tags (warns if first release)

2. **Environment Setup**
   - Installs Python and package manager
   - Installs dependencies including Commitizen

3. **Version Calculation**
   - Runs dry-run to calculate next version
   - Determines version increment based on commits

4. **Version Bump & Changelog**
   - Attempts `cz bump` (handles both version and changelog)
   - If it fails (e.g., first release), recovers by:
     - Generating full changelog
     - Bumping version with `--files-only`

5. **Git Operations**
   - Commits version changes
   - Creates version tag
   - Pushes to repository

6. **GitHub Release**
   - Creates GitHub release with auto-generated notes
   - Marks as draft or published based on input
   - Detects prerelease versions automatically

## Version Increment Types

### Standard Releases

| Increment | Example | Use Case |
|-----------|---------|----------|
| `patch` | 1.0.0 → 1.0.1 | Bug fixes, minor changes |
| `minor` | 1.0.1 → 1.1.0 | New features (backward compatible) |
| `major` | 1.1.0 → 2.0.0 | Breaking changes |

### Prerelease Versions

| Type | Example | Python Version Scheme |
|------|---------|----------------------|
| `alpha` | 1.0.0 → 1.0.1a0 | Alpha release |
| `beta` | 1.0.0 → 1.0.1b0 | Beta release |
| `rc` | 1.0.0 → 1.0.1rc0 | Release candidate |

Prereleases are automatically marked as "prerelease" on GitHub.

## Changelog Generation

### First Release (No Tags)

When no tags exist, the action generates a **full changelog** from all commits:

```markdown
## 0.1.0 (2024-01-18)

### Features

- feat: add user authentication
- feat: add database integration

### Bug Fixes

- fix: resolve login issue
```

### Subsequent Releases (1+ Tags)

With existing tags, the action generates an **incremental changelog** from the last tag:

```markdown
## 0.1.1 (2024-01-19)

### Bug Fixes

- fix: patch security vulnerability
```

## Examples

See [EXAMPLES.md](./EXAMPLES.md) for comprehensive examples covering:

- Different package managers (pip, uv, pixi)
- Version increment types
- Prerelease workflows
- Custom branches
- Multi-environment setups
- Integration patterns

## Permissions

The action requires `contents: write` permission:

```yaml
permissions:
  contents: write
```

This allows the action to:
- Push commits and tags
- Create GitHub releases

## Troubleshooting

### Error: "CHANGELOG.md file not found"

**Solution:** Create a CHANGELOG.md file at the expected location:

```bash
cat > CHANGELOG.md << 'EOF'
# Changelog

All notable changes to this project will be documented in this file.
EOF
git add CHANGELOG.md
git commit -m "docs: add changelog"
```

If using `config-file` for a monorepo sub-package, the changelog path is resolved **relative to the sub-package directory** (i.e. `dirname(config-file)`). Ensure the file configured under `changelog_file` exists inside that directory, not the repository root.

### Error: "No commits found"

**Cause:** No commits since the last tag.

**Solution:** Ensure you have new commits following conventional commit format:
- `feat:` for features
- `fix:` for bug fixes
- `docs:` for documentation
- etc.

### Error: "Failed to push changes to repository"

**Cause:** Missing upstream branch or permissions.

**Solution:**
1. Ensure `contents: write` permission is set
2. Branch should exist and be pushed to remote
3. Check if branch protection rules allow the action to push

### Changelog Not Updated

**Symptom:** Version bumped successfully but changelog file wasn't updated.

**Causes and Solutions:**

1. **Missing `update_changelog_on_bump = true`**

   The action will automatically detect this and generate the changelog manually. However, for optimal performance, add this to your `pyproject.toml`:

   ```toml
   [tool.commitizen]
   # ... other settings ...
   update_changelog_on_bump = true
   ```

2. **Custom changelog file path**

   If using a custom path (e.g., `docs/HISTORY.md`), ensure it's configured:

   ```toml
   [tool.commitizen]
   changelog_file = "docs/HISTORY.md"
   ```

   The action automatically detects and uses the configured path.

3. **No commits to add**

   If there are no conventional commits since the last release, the changelog won't have new entries.

### First Release Issues

For the first release, ensure:
1. Changelog file exists at the configured path (default: `CHANGELOG.md`)
2. At least one commit follows conventional format
3. No tags exist in the repository (or only one tag for second release)

## Related Documentation

- [Commitizen Documentation](https://commitizen-tools.github.io/commitizen/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [PEP 440 Version Identifiers](https://peps.python.org/pep-0440/)

## Support

For issues and feature requests, please use the [GitHub Issues](https://github.com/serapeum-org/github-actions/issues).
