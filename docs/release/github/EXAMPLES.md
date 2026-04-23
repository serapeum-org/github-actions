# GitHub Release Action - Detailed Examples

This document provides comprehensive examples for all use cases and scenarios of the GitHub Release action.

## Table of Contents

- [Basic Examples](#basic-examples)
- [Package Manager Examples](#package-manager-examples)
- [Version Increment Examples](#version-increment-examples)
- [Prerelease Examples](#prerelease-examples)
- [Custom Branch Examples](#custom-branch-examples)
- [Dependency Group Examples](#dependency-group-examples)
- [Draft Release Examples](#draft-release-examples)
- [Complete Workflow Examples](#complete-workflow-examples)
- [Monorepo Examples](#monorepo-examples)
- [Edge Cases and Special Scenarios](#edge-cases-and-special-scenarios)

---

## Basic Examples

### Minimal Configuration

The simplest possible release workflow:

```yaml
name: Release

on:
  workflow_dispatch:

permissions:
  contents: write

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - name: Create Release
        uses: serapeum-org/github-actions/actions/release/github@github-release/v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

**Behavior:**
- Uses default package manager (uv)
- Creates patch version bump (e.g., 1.0.0 → 1.0.1)
- Releases from `main` branch
- Publishes release immediately (not draft)

**Prerequisites:** Ensure your `pyproject.toml` has:

```toml
[tool.commitizen]
name = "cz_conventional_commits"
version = "0.1.0"
version_files = ["pyproject.toml:version"]
tag_format = "$version"
update_changelog_on_bump = true  # Recommended for automatic changelog updates
```

### Manual Release with Choice

Allow choosing version increment type:

```yaml
name: Manual Release

on:
  workflow_dispatch:
    inputs:
      increment:
        description: 'Version increment'
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
      - name: Create Release
        uses: serapeum-org/github-actions/actions/release/github@github-release/v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          increment: ${{ inputs.increment }}
```

---

## Package Manager Examples

### Using pip

```yaml
- name: Release with pip
  uses: serapeum-org/github-actions/actions/release/github@github-release/v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    package-manager: 'pip'
    python-version: '3.11'
    install-groups: 'groups: dev'
```

**Project setup (pyproject.toml):**

```toml
[dependency-groups]
dev = [
    "commitizen>=3.0.0",
    "pytest>=7.0.0",
]
```

### Using uv (Recommended)

```yaml
- name: Release with uv
  uses: serapeum-org/github-actions/actions/release/github@github-release/v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    package-manager: 'uv'
    python-version: '3.12'
    install-groups: 'groups: dev docs'
```

**Project setup (pyproject.toml):**

```toml
[dependency-groups]
dev = [
    "commitizen>=3.0.0",
    "pytest>=7.0.0",
]
docs = [
    "mkdocs>=1.5.0",
    "mkdocs-material>=9.0.0",
]
```

**With uv.lock:**

Ensure your repository has a `uv.lock` file:

```bash
uv lock
git add uv.lock
git commit -m "chore: add uv.lock"
```

### Using pixi

```yaml
- name: Release with pixi
  uses: serapeum-org/github-actions/actions/release/github@github-release/v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    package-manager: 'pixi'
    install-groups: 'default'
```

**Project setup (pixi.toml):**

```toml
[project]
name = "my-project"
version = "0.1.0"
channels = ["conda-forge"]

[dependencies]
python = ">=3.10"
commitizen = ">=3.0.0"

[tasks]
release = "cz bump"
```

---

## Version Increment Examples

### Patch Release (Bug Fixes)

```yaml
- name: Patch Release
  uses: serapeum-org/github-actions/actions/release/github@github-release/v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    increment: 'patch'
```

**Example:**
- Current: `1.2.3`
- New: `1.2.4`

**Commit types that trigger patch:**
```bash
git commit -m "fix: resolve authentication bug"
git commit -m "fix: patch memory leak"
```

### Minor Release (New Features)

```yaml
- name: Minor Release
  uses: serapeum-org/github-actions/actions/release/github@github-release/v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    increment: 'minor'
```

**Example:**
- Current: `1.2.4`
- New: `1.3.0`

**Commit types that trigger minor:**
```bash
git commit -m "feat: add user profile feature"
git commit -m "feat: implement OAuth login"
```

### Major Release (Breaking Changes)

```yaml
- name: Major Release
  uses: serapeum-org/github-actions/actions/release/github@github-release/v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    increment: 'major'
```

**Example:**
- Current: `1.3.0`
- New: `2.0.0`

**Commit types that trigger major:**
```bash
git commit -m "feat!: redesign API endpoints"
git commit -m "feat: remove deprecated methods

BREAKING CHANGE: The old auth methods are no longer supported"
```

---

## Prerelease Examples

### Alpha Release

```yaml
- name: Alpha Release
  uses: serapeum-org/github-actions/actions/release/github@github-release/v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    increment: 'patch'
    prerelease-type: 'alpha'
```

**Example:**
- Current: `1.0.0`
- New: `1.0.1a0` (first alpha)
- Next: `1.0.1a1` (second alpha)

**Use case:** Early development, internal testing

### Beta Release

```yaml
- name: Beta Release
  uses: serapeum-org/github-actions/actions/release/github@github-release/v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    increment: 'minor'
    prerelease-type: 'beta'
```

**Example:**
- Current: `1.0.0`
- New: `1.1.0b0` (first beta)
- Next: `1.1.0b1` (second beta)

**Use case:** Feature complete, external testing

### Release Candidate

```yaml
- name: Release Candidate
  uses: serapeum-org/github-actions/actions/release/github@github-release/v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    increment: 'major'
    prerelease-type: 'rc'
```

**Example:**
- Current: `1.5.0`
- New: `2.0.0rc0` (first RC)
- Next: `2.0.0rc1` (second RC)

**Use case:** Final testing before production release

### Prerelease Workflow Example

Complete workflow with multiple prerelease stages:

```yaml
name: Prerelease Workflow

on:
  workflow_dispatch:
    inputs:
      stage:
        description: 'Release stage'
        required: true
        type: choice
        options:
          - alpha
          - beta
          - rc
          - final

permissions:
  contents: write

jobs:
  prerelease:
    if: ${{ inputs.stage != 'final' }}
    runs-on: ubuntu-latest
    steps:
      - name: Create Prerelease
        uses: serapeum-org/github-actions/actions/release/github@github-release/v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          increment: 'minor'
          prerelease-type: ${{ inputs.stage }}
          draft: 'false'

  final-release:
    if: ${{ inputs.stage == 'final' }}
    runs-on: ubuntu-latest
    steps:
      - name: Create Final Release
        uses: serapeum-org/github-actions/actions/release/github@github-release/v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          increment: 'minor'
          prerelease-type: 'none'
```

---

## Custom Branch Examples

### Release from Develop Branch

```yaml
- name: Release from Develop
  uses: serapeum-org/github-actions/actions/release/github@github-release/v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    release-branch: 'develop'
    increment: 'patch'
```

### Release from Version Branch

```yaml
- name: Release v2.x
  uses: serapeum-org/github-actions/actions/release/github@github-release/v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    release-branch: 'release/v2.0'
    increment: 'patch'
```

### Multi-Branch Release Strategy

```yaml
name: Multi-Branch Releases

on:
  workflow_dispatch:
    inputs:
      branch:
        description: 'Release branch'
        required: true
        type: choice
        options:
          - main
          - develop
          - release/v2.0

permissions:
  contents: write

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - name: Create Release
        uses: serapeum-org/github-actions/actions/release/github@github-release/v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          release-branch: ${{ inputs.branch }}
          increment: 'patch'
```

---

## Dependency Group Examples

### Install Specific Groups

```yaml
- name: Release with Dev and Docs Groups
  uses: serapeum-org/github-actions/actions/release/github@github-release/v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    install-groups: 'groups: dev docs'
```

**Project setup:**

```toml
[dependency-groups]
dev = [
    "commitizen>=3.0.0",
    "pytest>=7.0.0",
    "mypy>=1.0.0",
]
docs = [
    "mkdocs>=1.5.0",
    "mkdocs-material>=9.0.0",
]
```

### Install Optional Dependencies (Extras)

```yaml
- name: Release with Extras
  uses: serapeum-org/github-actions/actions/release/github@github-release/v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    install-groups: 'extras: aws viz'
```

**Project setup:**

```toml
[project.optional-dependencies]
aws = [
    "boto3>=1.26.0",
    "botocore>=1.29.0",
]
viz = [
    "matplotlib>=3.5.0",
    "plotly>=5.0.0",
]
```

### Combine Groups and Extras

```yaml
- name: Release with Groups and Extras
  uses: serapeum-org/github-actions/actions/release/github@github-release/v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    install-groups: 'groups: dev docs, extras: aws'
```

### Core Dependencies Only

```yaml
- name: Release with Core Only
  uses: serapeum-org/github-actions/actions/release/github@github-release/v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    install-groups: ''
```

**Note:** Ensure Commitizen is in core dependencies:

```toml
[project]
dependencies = [
    "commitizen>=3.0.0",
    "requests>=2.28.0",
]
```

---

## Draft Release Examples

### Create Draft for Review

```yaml
- name: Create Draft Release
  uses: serapeum-org/github-actions/actions/release/github@github-release/v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    increment: 'minor'
    draft: 'true'
```

**Use case:**
- Review release notes before publishing
- Wait for additional checks/approvals
- Manual testing before announcement

### Automatic Draft, Manual Publish

```yaml
name: Draft Release

on:
  push:
    branches: [main]

permissions:
  contents: write

jobs:
  draft:
    runs-on: ubuntu-latest
    steps:
      - name: Create Draft
        uses: serapeum-org/github-actions/actions/release/github@github-release/v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          draft: 'true'

      - name: Notify Team
        run: |
          echo "Draft release created. Review at:"
          echo "${{ github.server_url }}/${{ github.repository }}/releases"
```

**Manual publish:**
1. Go to GitHub Releases page
2. Find the draft release
3. Click "Edit"
4. Review release notes
5. Click "Publish release"

---

## Complete Workflow Examples

### Production Release Pipeline

```yaml
name: Production Release

on:
  workflow_dispatch:
    inputs:
      increment:
        description: 'Version increment'
        required: true
        type: choice
        options:
          - patch
          - minor
          - major
      confirm:
        description: 'Type "yes" to confirm'
        required: true

permissions:
  contents: write

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Validate Confirmation
        if: ${{ inputs.confirm != 'yes' }}
        run: |
          echo "::error::Release cancelled - confirmation required"
          exit 1

  test:
    needs: validate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5

      - name: Run Tests
        run: |
          pip install -e ".[dev]"
          pytest

  release:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Create GitHub Release
        uses: serapeum-org/github-actions/actions/release/github@github-release/v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          increment: ${{ inputs.increment }}
          package-manager: 'uv'
          python-version: '3.12'

      - name: Notify Success
        run: |
          echo "✅ Release ${{ steps.release.outputs.NEW_VERSION }} created"
```

### Automated Weekly Beta Releases

```yaml
name: Weekly Beta Release

on:
  schedule:
    - cron: '0 10 * * 1'  # Every Monday at 10 AM UTC
  workflow_dispatch:

permissions:
  contents: write

jobs:
  beta:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
        with:
          fetch-depth: 0

      - name: Check for New Commits
        id: check
        run: |
          LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
          if [ -z "$LAST_TAG" ]; then
            echo "has_changes=true" >> $GITHUB_OUTPUT
          else
            CHANGES=$(git log $LAST_TAG..HEAD --oneline)
            if [ -n "$CHANGES" ]; then
              echo "has_changes=true" >> $GITHUB_OUTPUT
            else
              echo "has_changes=false" >> $GITHUB_OUTPUT
            fi
          fi

      - name: Create Beta Release
        if: steps.check.outputs.has_changes == 'true'
        uses: serapeum-org/github-actions/actions/release/github@github-release/v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          increment: 'patch'
          prerelease-type: 'beta'

      - name: Skip Message
        if: steps.check.outputs.has_changes == 'false'
        run: echo "No changes since last release, skipping"
```

### Multi-Python Version Release

```yaml
name: Multi-Python Release

on:
  workflow_dispatch:

permissions:
  contents: write

jobs:
  test:
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Run Tests
        run: |
          pip install -e ".[dev]"
          pytest

  release:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Create Release
        uses: serapeum-org/github-actions/actions/release/github@github-release/v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          python-version: '3.12'  # Use latest for release
          increment: 'patch'
```

### GitFlow Release Pattern

```yaml
name: GitFlow Release

on:
  push:
    branches:
      - main
      - develop
      - 'release/**'

permissions:
  contents: write

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - name: Determine Release Type
        id: type
        run: |
          BRANCH="${{ github.ref_name }}"
          if [[ "$BRANCH" == "main" ]]; then
            echo "increment=patch" >> $GITHUB_OUTPUT
            echo "prerelease=none" >> $GITHUB_OUTPUT
            echo "draft=false" >> $GITHUB_OUTPUT
          elif [[ "$BRANCH" == "develop" ]]; then
            echo "increment=patch" >> $GITHUB_OUTPUT
            echo "prerelease=beta" >> $GITHUB_OUTPUT
            echo "draft=false" >> $GITHUB_OUTPUT
          else
            echo "increment=patch" >> $GITHUB_OUTPUT
            echo "prerelease=rc" >> $GITHUB_OUTPUT
            echo "draft=true" >> $GITHUB_OUTPUT
          fi

      - name: Create Release
        uses: serapeum-org/github-actions/actions/release/github@github-release/v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          release-branch: ${{ github.ref_name }}
          increment: ${{ steps.type.outputs.increment }}
          prerelease-type: ${{ steps.type.outputs.prerelease }}
          draft: ${{ steps.type.outputs.draft }}
```

---

## Monorepo Examples

### Release a Sub-Package with Its Own Config

For monorepos where each package manages its own version and changelog:

```yaml
- name: Release sub-package
  uses: serapeum-org/github-actions/actions/release/github@github-release/v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    increment: 'minor'
    package-manager: 'uv'
    install-groups: 'groups: dev'
    config-file: 'libs/my-package/pyproject.toml'
```

**Sub-package commitizen config (`libs/my-package/pyproject.toml`):**

```toml
[tool.commitizen]
name = "cz_conventional_commits"
version = "0.1.0"
# All paths are relative to libs/my-package/, not the repo root
version_files = ["pyproject.toml:version"]
tag_format = "my-package-$version"
update_changelog_on_bump = true
changelog_file = "docs/CHANGELOG.md"
```

**Important:** Because the action changes into `libs/my-package/` before running Commitizen, every path in that section must be relative to `libs/my-package/`. Using the full repo-relative path (e.g. `libs/my-package/pyproject.toml:version`) would fail.

### Multi-Package Monorepo Release Workflow

Release multiple independent packages in one workflow:

```yaml
name: Monorepo Release

on:
  workflow_dispatch:
    inputs:
      package:
        description: 'Package to release'
        required: true
        type: choice
        options:
          - libs/pkg-a
          - libs/pkg-b
          - libs/pkg-c
      increment:
        description: 'Version increment'
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
      - name: Create Release
        uses: serapeum-org/github-actions/actions/release/github@github-release/v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          increment: ${{ inputs.increment }}
          config-file: '${{ inputs.package }}/pyproject.toml'
```

---

## Edge Cases and Special Scenarios

### First Release (No Existing Tags)

**Scenario:** Creating the very first release of a project

```yaml
- name: First Release
  uses: serapeum-org/github-actions/actions/release/github@github-release/v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    increment: 'patch'
```

**Requirements:**
1. CHANGELOG.md must exist (can be empty)
2. At least one conventional commit
3. Commitizen configured in pyproject.toml

**Behavior:**
- Generates full changelog from all commits
- Creates first tag (e.g., 0.1.0)
- Warning shown (not an error)

**Setup:**

```bash
# Create CHANGELOG.md
cat > CHANGELOG.md << 'EOF'
# Changelog

All notable changes to this project will be documented in this file.
EOF

# Commit with conventional format
git add CHANGELOG.md
git commit -m "docs: add changelog"

# Make some changes
git commit -m "feat: initial implementation"
git commit -m "fix: resolve setup issue"
```

### Project Without Dependency Groups

**Scenario:** Minimal project with only core dependencies

```yaml
- name: Release Minimal Project
  uses: serapeum-org/github-actions/actions/release/github@github-release/v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    install-groups: ''
```

**Project setup:**

```toml
[project]
name = "minimal-project"
version = "0.1.0"
dependencies = [
    "commitizen>=3.0.0",  # Required!
    "requests>=2.28.0",
]

[tool.commitizen]
name = "cz_conventional_commits"
version = "0.1.0"
version_files = ["pyproject.toml:version"]
tag_format = "$version"
```

### Recovering from Failed Release

**Scenario:** Previous release attempt failed, need to retry

```bash
# Check current state
git status
git log --oneline -5

# If version was bumped but not pushed
git reset --soft HEAD~1  # Undo commit
git restore --staged .   # Unstage changes

# If tag was created locally
git tag -d 1.2.3  # Delete local tag

# Clean state, retry release
```

**Prevention:** Use draft releases for testing:

```yaml
- name: Safe Release
  uses: serapeum-org/github-actions/actions/release/github@github-release/v1
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
    draft: 'true'  # Safe to retry
```

### Cross-Platform Release

**Scenario:** Ensure release works on all platforms

```yaml
name: Cross-Platform Release

on:
  workflow_dispatch:

permissions:
  contents: write

jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v5
      - name: Test on ${{ matrix.os }}
        run: |
          pip install -e ".[dev]"
          pytest

  release:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Create Release
        uses: serapeum-org/github-actions/actions/release/github@github-release/v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

### Hotfix Release Pattern

**Scenario:** Emergency fix on production

```yaml
name: Hotfix Release

on:
  push:
    branches:
      - 'hotfix/**'

permissions:
  contents: write

jobs:
  hotfix:
    runs-on: ubuntu-latest
    steps:
      - name: Create Hotfix Release
        uses: serapeum-org/github-actions/actions/release/github@github-release/v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          release-branch: ${{ github.ref_name }}
          increment: 'patch'
          draft: 'false'

      - name: Cherry-pick to Main
        run: |
          git checkout main
          git cherry-pick ${{ github.sha }}
          git push origin main
```

### Release with Build Artifacts

**Scenario:** Attach build artifacts to release

```yaml
name: Release with Artifacts

on:
  workflow_dispatch:

permissions:
  contents: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5

      - name: Build Distribution
        run: |
          pip install build
          python -m build

      - name: Upload Artifacts
        uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/

  release:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Download Artifacts
        uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/

      - name: Create Release
        uses: serapeum-org/github-actions/actions/release/github@github-release/v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}

      - name: Upload Release Assets
        uses: softprops/action-gh-release@v2
        with:
          files: dist/*
          tag_name: ${{ steps.release.outputs.NEW_VERSION }}
```

### Release with Changelog Validation

**Scenario:** Ensure changelog follows format

```yaml
name: Validated Release

on:
  workflow_dispatch:

permissions:
  contents: write

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
        with:
          fetch-depth: 0

      - name: Validate Commits
        run: |
          pip install commitizen
          cz check --rev-range $(git describe --tags --abbrev=0)..HEAD

  release:
    needs: validate
    runs-on: ubuntu-latest
    steps:
      - name: Create Release
        uses: serapeum-org/github-actions/actions/release/github@github-release/v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

---

## Best Practices Summary

### 1. **Always Use Draft for Production**

Start with draft releases for important deployments:

```yaml
draft: 'true'
```

### 2. **Validate Before Release**

Run tests and checks before creating releases:

```yaml
jobs:
  test:
    # ... run tests

  release:
    needs: test
    # ... create release
```

### 3. **Use Conventional Commits**

Ensure all commits follow the convention:

```bash
feat: add new feature
fix: resolve bug
docs: update documentation
chore: update dependencies
```

### 4. **Maintain CHANGELOG.md**

Keep a changelog file in your repository (required).

### 5. **Test with Prereleases**

Use alpha/beta/rc for testing before final release:

```yaml
prerelease-type: 'beta'
```

### 6. **Use Version Tags**

Reference specific action versions:

```yaml
uses: serapeum-org/github-actions/actions/release/github@github-release/v1.0.0
```

### 7. **Set Proper Permissions**

Always include required permissions:

```yaml
permissions:
  contents: write
```

---

## Troubleshooting Examples

See the main [README.md](./README.md) for common issues and solutions.

## Additional Resources

- [Action Source Code](../../../actions/release/github/action.yml)
- [Test Workflows](../../../.github/workflows/test-release-github.yml)
- [Commitizen Documentation](https://commitizen-tools.github.io/commitizen/)
