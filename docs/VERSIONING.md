# Versioning Guide for GitHub Actions

This document explains the versioning strategy used in this repository for publishing and maintaining GitHub Actions.

## Table of Contents

- [Overview](#overview)
- [Semantic Versioning](#semantic-versioning)
- [Tag Strategy](#tag-strategy)
  - [Global Versioning Strategy](#global-versioning-strategy)
  - [Namespaced Versioning Strategy](#namespaced-versioning-strategy)
- [Release Process](#release-process)
  - [Global Versioning Release Process](#global-versioning-release-process)
  - [Namespaced Versioning Release Process](#namespaced-versioning-release-process)
- [Moving Major Version Tags](#moving-major-version-tags)
- [Usage for Consumers](#usage-for-consumers)
- [Breaking Changes](#breaking-changes)
- [Examples](#examples)

## Overview

This repository contains reusable GitHub Actions (composite actions). Unlike traditional software packages, GitHub Actions use a **tag-based versioning system** where users reference specific versions directly in their workflows.

This repository supports **two versioning strategies**:

1. **Global Versioning**: All actions share the same version tags (e.g., `v1`, `v2`)
2. **Namespaced Versioning**: Each action has independent version tags (e.g., `python-setup/pip/v1.0.0`, `mkdocs-deploy/v1.0.0`)

**Key Principles:**
- ✅ Use semantic versioning (e.g., `v1.0.0`, `v1.1.0`, `v2.0.0`)
- ✅ Maintain moving major version tags (e.g., `v1`, `v2`) for convenience
- ✅ Keep specific version tags immutable (e.g., `v1.0.0` never changes)
- ✅ Use `v` prefix for all version tags
- ✅ Use namespaced tags for independent action versioning (e.g., `action-name/v1.0.0`)

## Semantic Versioning

We follow [Semantic Versioning 2.0.0](https://semver.org/) with the format: `vMAJOR.MINOR.PATCH`

### Version Components

```
v1.2.3
│ │ │
│ │ └── PATCH: Bug fixes, documentation updates (backward compatible)
│ └──── MINOR: New features, improvements (backward compatible)
└────── MAJOR: Breaking changes (NOT backward compatible)
```

### When to Increment

| Version | Increment When | Examples |
|---------|---------------|----------|
| **PATCH** | Bug fixes, docs, internal refactoring | `v1.0.0` → `v1.0.1` |
| **MINOR** | New features, new inputs (optional), deprecations | `v1.0.1` → `v1.1.0` |
| **MAJOR** | Breaking changes, removed features, required inputs changed | `v1.1.0` → `v2.0.0` |

### Examples of Changes

#### PATCH Version (v1.0.0 → v1.0.1)
- 🐛 Fix a bug in cache key generation
- 📝 Update documentation
- 🔧 Internal code refactoring
- ⚡ Performance improvements (no behavior change)

#### MINOR Version (v1.0.1 → v1.1.0)
- ✨ Add new optional input parameter
- 🎉 Add new feature that doesn't affect existing usage
- 📊 Add new logging/output
- ⚠️ Deprecate a feature (but still works)

#### MAJOR Version (v1.1.0 → v2.0.0)
- 💥 Remove or rename an input parameter
- 💥 Change default behavior significantly
- 💥 Remove deprecated features
- 💥 Change required inputs or validation rules
- 💥 Update to incompatible dependency versions

## Tag Strategy

This repository supports two versioning strategies. Choose the one that best fits your needs:

### Global Versioning Strategy

In this strategy, **all actions in the repository share the same version tags**. When you release `v1.0.0`, it applies to all actions.

**Use when:**
- ✅ All actions are released together
- ✅ Actions have dependencies on each other
- ✅ Simpler to manage for small repositories

**Tag format:** `v1.0.0`, `v1`, `v2`

**Usage example:**
```yaml
- uses: serapeum-org/github-actions/actions/python-setup/pip@v1
- uses: serapeum-org/github-actions/actions/mkdocs-deploy@v1
```

### Namespaced Versioning Strategy

In this strategy, **each action has its own independent version tags**. You can release `python-setup/pip/v1.0.1` without affecting other actions.

**Use when:**
- ✅ Actions evolve independently
- ✅ You want granular version control
- ✅ Different actions have different release cycles
- ✅ You need clear versioning per action

**Tag format:** `action-name/v1.0.0`, `action-name/v1`, `action-name/v2`

**Examples:**
- `python-setup/pip/v1.0.0`, `python-setup/pip/v1`
- `python-setup/uv/v1.0.0`, `python-setup/uv/v1`
- `python-setup/pixi/v1.0.0`, `python-setup/pixi/v1`
- `mkdocs-deploy/v1.0.0`, `mkdocs-deploy/v1`

**Usage example:**
```yaml
- uses: serapeum-org/github-actions/actions/python-setup/pip@python-setup/pip/v1
- uses: serapeum-org/github-actions/actions/mkdocs-deploy@mkdocs-deploy/v1.0.0
```

**Benefits:**
- Each action can be versioned independently
- Update one action without affecting others
- Clear version history per action
- No breaking changes across unrelated actions

---

## Tag Types (Both Strategies)

We maintain two types of Git tags:

#### 1. Specific Version Tags (Immutable)

**Global Format:** `v1.0.0`, `v1.1.0`, `v1.2.0`, `v2.0.0`  
**Namespaced Format:** `action-name/v1.0.0`, `action-name/v1.1.0`, `action-name/v2.0.0`

**Characteristics:**
- ✅ Never moved or changed
- ✅ Point to a specific commit forever
- ✅ Used for reproducibility and security
- ✅ Ideal for production workflows

**Examples:**
```yaml
# Global versioning - Pin to exact version
- uses: serapeum-org/github-actions/actions/python-setup/pixi@v1.0.0

# Namespaced versioning - Pin to exact version
- uses: serapeum-org/github-actions/actions/python-setup/pip@python-setup/pip/v1.0.1
```

#### 2. Major Version Tags (Moving)

**Global Format:** `v1`, `v2`, `v3`  
**Namespaced Format:** `action-name/v1`, `action-name/v2`, `action-name/v3`

**Characteristics:**
- 🔄 Updated with each new release within the major version
- 🔄 Points to the latest compatible version
- 🔄 Used for automatic updates
- ⚠️ May change behavior (but stays backward compatible)

**Examples:**
```yaml
# Global versioning - Use major version for updates
- uses: serapeum-org/github-actions/actions/python-setup/pixi@v1

# Namespaced versioning - Use major version for updates
- uses: serapeum-org/github-actions/actions/mkdocs-deploy@mkdocs-deploy/v1
```

### Visual Representation

```
Timeline of commits and tags:

A ---- B ---- C ---- D ---- E ---- F
       ↑      ↑            ↑      ↑
       │      │            │      │
    v1.0.0  v1.1.0      v1.2.0  v2.0.0
       ↑                   ↑      ↑
       v1 (initially)      │      v2
                           │
                      v1 (moved)
                      
After release flow:
- v1.0.0: Created v1 and v1.0.0 pointing to commit B
- v1.1.0: Created v1.1.0 at commit C, kept v1.0.0 at B
- v1.2.0: Created v1.2.0 at commit E, moved v1 from B to E
- v2.0.0: Created v2 and v2.0.0 pointing to commit F
```

## Release Process

### Global Versioning Release Process

Use this process when all actions share the same version tags.

#### Step-by-Step Guide

##### 1. Prepare the Release

Make and commit your changes:

```bash
# Make your changes
git add .
git commit -m "feat: add caching support to pixi action"
git push origin main
```

##### 2. Create Specific Version Tag

```bash
# Create an annotated tag
git tag -a v1.1.0 -m "Release v1.1.0

- Add caching support for faster CI runs
- Improve error messages for missing lock files
- Update documentation with caching examples"

# Push the tag
git push origin v1.1.0
```

##### 3. Create or Move Major Version Tag

```bash
# Move the major version tag to the new release
git tag -fa v1 -m "Update v1 to v1.1.0"

# Force push (required because we're overwriting an existing tag)
git push origin v1 --force
```

##### 4. Create GitHub Release

**Option A: Using GitHub CLI**

```bash
gh release create v1.1.0 \
  --title "v1.1.0 - Caching Support" \
  --notes "## 🎉 New Features

- **Caching**: Enable environment caching with \`cache: 'true'\`
- **Improved Errors**: Better error messages for common issues

## 📝 Documentation

- Updated pixi.md with caching examples
- Added troubleshooting section

## 🔧 Internal

- Refactored validation logic
- Added integration tests for caching

## 📦 Upgrade Notes

This is a backward-compatible release. Simply update your action reference from \`@v1.0.0\` to \`@v1.1.0\` or use \`@v1\` for automatic updates."
```

**Option B: Using GitHub Web UI**

1. Go to your repository on GitHub
2. Click **"Releases"** → **"Draft a new release"**
3. Click **"Choose a tag"** → Select `v1.1.0`
4. Set **"Release title"**: `v1.1.0 - Caching Support`
5. Write **release notes** (see format above)
6. Click **"Publish release"**

### Namespaced Versioning Release Process

Use this process to version individual actions independently.

#### Step-by-Step Guide

##### 1. Prepare the Release

Make and commit your changes to the specific action:

```bash
# Make your changes to actions/python-setup/pip/
git add actions/python-setup/pip/
git commit -m "feat(python-setup/pip): add support for dependency groups"
git push origin main
```

##### 2. Create Namespaced Specific Version Tag

```bash
# Create an annotated tag with namespace prefix
git tag -a pip/v1.0.1 -m "Release pip v1.0.1

- Add support for PEP 735 dependency groups
- Fix cache key generation on Windows
- Improve error messages"

# Push the tag
git push origin pip/v1.0.1
```

##### 3. Create or Move Namespaced Major Version Tag

```bash
# Move the major version tag for this specific action
git tag -fa pip/v1 -m "Update pip v1 to v1.0.1"

# Force push (required because we're overwriting an existing tag)
git push origin pip/v1 --force
```

##### 4. Create GitHub Release

**Option A: Using GitHub CLI**

```bash
gh release create python-setup/pip/v1.0.1 \
  --title "python-setup/pip v1.0.1" \
  --notes "## 🎉 New Features

- **Dependency Groups**: Support for PEP 735 dependency groups
- **Improved Caching**: Better cache key generation on Windows

## 📦 Upgrade Notes

This is a backward-compatible release for \`python-setup/pip\` action only.

Update your workflow:
\`\`\`yaml
- uses: serapeum-org/github-actions/actions/python-setup/pip@python-setup/pip/v1.0.1
  # or use @python-setup/pip/v1 for automatic updates
\`\`\`"
```

**Option B: Using GitHub Web UI**

1. Go to your repository on GitHub
2. Click **"Releases"** → **"Draft a new release"**
3. Click **"Choose a tag"** → Select `python-setup/pip/v1.0.1`
4. Set **"Release title"**: `python-setup/pip v1.0.1`
5. Write **release notes** with action name prefix
6. Click **"Publish release"**

### Automated Release Workflow

#### Global Versioning Workflow

Create `.github/workflows/release.yml` for global versioning:

```yaml
name: Create Release

on:
  push:
    tags:
      - 'v*.*.*'

permissions:
  contents: write

jobs:
  release:
    name: Create Release
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Get version info
        id: version
        run: |
          TAG=${GITHUB_REF#refs/tags/}
          MAJOR_VERSION=$(echo $TAG | cut -d. -f1)
          echo "tag=$TAG" >> $GITHUB_OUTPUT
          echo "major=$MAJOR_VERSION" >> $GITHUB_OUTPUT

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          generate_release_notes: true
          draft: false
          prerelease: false

      - name: Update major version tag
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git tag -fa ${{ steps.version.outputs.major }} -m "Update ${{ steps.version.outputs.major }} to ${{ steps.version.outputs.tag }}"
          git push origin ${{ steps.version.outputs.major }} --force
```

**How it works:**
1. Push a version tag: `git push origin v1.1.0`
2. Workflow automatically:
   - Creates a GitHub release
   - Generates release notes from commits
   - Moves the major version tag (`v1`)

#### Namespaced Versioning Workflow

Create `.github/workflows/release-namespaced.yml` for namespaced versioning:

```yaml
name: Create Namespaced Release

on:
  push:
    tags:
      - '*/v*.*.*'  # Matches tags like python-setup/pip/v1.0.1

permissions:
  contents: write

jobs:
  release:
    name: Create Release
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Get version info
        id: version
        run: |
          TAG=${GITHUB_REF#refs/tags/}
          # Extract action name (everything before /vX.Y.Z)
          ACTION_NAME=$(echo $TAG | sed 's|/v[0-9].*||')
          # Extract version (vX.Y.Z)
          VERSION=$(echo $TAG | grep -oP 'v[0-9]+\.[0-9]+\.[0-9]+$')
          # Extract major version (vX)
          MAJOR_VERSION=$(echo $VERSION | cut -d. -f1)
          
          echo "tag=$TAG" >> $GITHUB_OUTPUT
          echo "action=$ACTION_NAME" >> $GITHUB_OUTPUT
          echo "version=$VERSION" >> $GITHUB_OUTPUT
          echo "major=$ACTION_NAME/$MAJOR_VERSION" >> $GITHUB_OUTPUT

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          name: "${{ steps.version.outputs.action }} ${{ steps.version.outputs.version }}"
          generate_release_notes: true
          draft: false
          prerelease: false

      - name: Update major version tag
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git tag -fa ${{ steps.version.outputs.major }} -m "Update ${{ steps.version.outputs.major }} to ${{ steps.version.outputs.tag }}"
          git push origin ${{ steps.version.outputs.major }} --force
```

**How it works:**
1. Push a namespaced tag: `git push origin python-setup/pip/v1.0.1`
2. Workflow automatically:
   - Creates a GitHub release with action-specific title
   - Generates release notes from commits
   - Moves the major version tag (`python-setup/pip/v1`)

## Moving Major Version Tags

### What Does "Moving" Mean?

**Moving a tag** means updating a Git tag to point to a different commit. This is done by:
1. Deleting the old tag (with `-f` flag)
2. Creating a new tag with the same name at a different commit
3. Force-pushing to overwrite the remote tag

### Why Move Major Version Tags?

This allows users to:
- ✅ Get automatic bug fixes and features
- ✅ Stay within a major version (no breaking changes)
- ✅ Avoid updating workflow files for every patch/minor release

### Commands Explained

```bash
# -f  = force (allows overwriting existing tag)
# -a  = annotated (creates tag with metadata)
git tag -fa v1 -m "Update v1 to v1.1.0"

# --force = required to overwrite remote tag
git push origin v1 --force
```

### Example Flow

**Initial Release (v1.0.0):**
```bash
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0

git tag -a v1 -m "Major version v1 -> v1.0.0"
git push origin v1
```

Result: Both `v1` and `v1.0.0` point to the same commit.

**Bug Fix Release (v1.0.1):**
```bash
git tag -a v1.0.1 -m "Release v1.0.1"
git push origin v1.0.1

# Move v1 to point to v1.0.1
git tag -fa v1 -m "Update v1 -> v1.0.1"
git push origin v1 --force
```

Result: 
- `v1.0.0` → Still points to old commit
- `v1.0.1` → Points to new commit
- `v1` → Now points to new commit (moved)

**New Feature Release (v1.1.0):**
```bash
git tag -a v1.1.0 -m "Release v1.1.0"
git push origin v1.1.0

# Move v1 again
git tag -fa v1 -m "Update v1 -> v1.1.0"
git push origin v1 --force
```

Result: `v1` now points to v1.1.0 (moved again).

**Breaking Change Release (v2.0.0):**
```bash
git tag -a v2.0.0 -m "Release v2.0.0"
git push origin v2.0.0

# Create NEW major version tag (don't move v1)
git tag -a v2 -m "Major version v2 -> v2.0.0"
git push origin v2
```

Result: 
- `v1` → Still points to v1.1.0
- `v2` → Points to v2.0.0 (new tag)
- Users must explicitly update to `@v2`

## Usage for Consumers

### Referencing Actions

Users can reference your actions in three ways:

#### Option 1: Specific Version (Recommended for Production)

```yaml
- uses: serapeum-org/github-actions/actions/python-setup/pixi@v1.0.0
```

**Pros:**
- ✅ Completely stable and reproducible
- ✅ Never changes unexpectedly
- ✅ Best for security-critical workflows

**Cons:**
- ❌ Doesn't get bug fixes automatically
- ❌ Must manually update for new features

**Best for:** Production, security-sensitive, compliance-required workflows

#### Option 2: Major Version (Recommended for Most Users)

```yaml
- uses: serapeum-org/github-actions/actions/python-setup/pixi@v1
```

**Pros:**
- ✅ Gets bug fixes automatically
- ✅ Gets new features automatically (within v1.x.x)
- ✅ No breaking changes

**Cons:**
- ❌ Behavior may change slightly
- ❌ Requires trust in maintainers

**Best for:** Most workflows, active development, CI/CD pipelines

#### Option 3: Branch (Not Recommended)

```yaml
- uses: serapeum-org/github-actions/actions/python-setup/pixi@main
```

**Pros:**
- ✅ Always latest code

**Cons:**
- ❌ Can break at any time
- ❌ Includes breaking changes
- ❌ Not reproducible

**Best for:** Testing unreleased features, development only

### Recommendation Matrix

| Use Case | Recommended Reference | Example |
|----------|----------------------|---------|
| Production workflows | Specific version | `@v1.0.0` |
| CI/CD pipelines | Major version | `@v1` |
| Active development | Major version | `@v1` |
| Security-critical | Specific version | `@v1.0.0` |
| Testing new features | Branch | `@main` |
| Dependabot/Renovate | Major version | `@v1` |

## Breaking Changes

### What Constitutes a Breaking Change?

A breaking change requires a **major version bump** (e.g., v1.x.x → v2.0.0).

#### Breaking Changes (Require v2.0.0):

- ❌ Removing an input parameter
- ❌ Renaming an input parameter
- ❌ Changing an input from optional to required
- ❌ Changing default values that affect behavior
- ❌ Removing or renaming outputs
- ❌ Changing behavior in incompatible ways
- ❌ Dropping support for older versions (e.g., Python 3.7)
- ❌ Changing error handling that could break workflows

#### NOT Breaking Changes (Can be v1.1.0):

- ✅ Adding new optional input parameters
- ✅ Adding new outputs
- ✅ Deprecating features (but still working)
- ✅ Bug fixes that restore intended behavior
- ✅ Performance improvements
- ✅ Documentation updates
- ✅ Adding new features that don't affect existing usage

### Handling Breaking Changes

#### 1. Deprecation Period (Preferred)

Before making a breaking change, deprecate in a minor version:

**v1.5.0 - Deprecation:**
```yaml
inputs:
  old-name:
    description: 'DEPRECATED: Use new-name instead'
    required: false
```

Add warning in action:
```yaml
- name: Deprecation warning
  if: inputs.old-name != ''
  shell: bash
  run: |
    echo "::warning::Input 'old-name' is deprecated and will be removed in v2.0.0. Use 'new-name' instead."
```

**v2.0.0 - Removal:**
```yaml
inputs:
  new-name:
    description: 'Replacement for old-name'
    required: false
```

#### 2. Migration Guide

Always provide a migration guide in the release notes:

```markdown
## 💥 Breaking Changes in v2.0.0

### Removed `cache-key` input

The `cache-key` input has been removed. Caching now uses an automatic key based on `pixi.lock`.

**Migration:**

```diff
- uses: serapeum-org/github-actions/actions/python-setup/pixi@v1
  with:
-   cache-key: custom-key
    cache: 'true'
```

The action will automatically generate an optimal cache key.

### Changed `verify-lock` default

The default for `verify-lock` changed from `'false'` to `'true'`.

**Migration:**

If you want the old behavior:

```yaml
- uses: serapeum-org/github-actions/actions/python-setup/pixi@v2
  with:
    verify-lock: 'false'  # Explicit old behavior
```
```

## Examples

### Global Versioning Examples

#### Example 1: First Release

```bash
# Initial release
git tag -a v1.0.0 -m "Release v1.0.0: Initial release"
git push origin v1.0.0

git tag -a v1 -m "Major version v1"
git push origin v1

gh release create v1.0.0 --title "v1.0.0 - Initial Release" --generate-notes
```

#### Example 2: Bug Fix

```bash
# Bug fix release
git tag -a v1.0.1 -m "Release v1.0.1: Fix cache key generation"
git push origin v1.0.1

# Move v1 to include the fix
git tag -fa v1 -m "Update v1 to v1.0.1"
git push origin v1 --force

gh release create v1.0.1 --title "v1.0.1 - Bug Fixes" --notes "Fix cache key generation for Windows"
```

#### Example 3: New Feature

```bash
# New feature release
git tag -a v1.1.0 -m "Release v1.1.0: Add caching support"
git push origin v1.1.0

# Move v1 to include the feature
git tag -fa v1 -m "Update v1 to v1.1.0"
git push origin v1 --force

gh release create v1.1.0 --title "v1.1.0 - Caching Support" --generate-notes
```

#### Example 4: Breaking Change

```bash
# Breaking change release
git tag -a v2.0.0 -m "Release v2.0.0: Remove deprecated inputs"
git push origin v2.0.0

# Create NEW major version tag (don't touch v1)
git tag -a v2 -m "Major version v2"
git push origin v2

gh release create v2.0.0 --title "v2.0.0 - Breaking Changes" --notes "See MIGRATION.md for upgrade guide"
```

### Namespaced Versioning Examples

#### Example 1: First Release of Specific Action

```bash
# Initial release of python-setup/pip action
git tag -a python-setup/pip/v1.0.0 -m "Release python-setup/pip v1.0.0: Initial release"
git push origin python-setup/pip/v1.0.0

git tag -a python-setup/pip/v1 -m "Major version python-setup/pip v1"
git push origin python-setup/pip/v1

gh release create python-setup/pip/v1.0.0 \
  --title "python-setup/pip v1.0.0 - Initial Release" \
  --generate-notes
```

#### Example 2: Bug Fix for Specific Action

```bash
# Bug fix release for python-setup/pip
git tag -a python-setup/pip/v1.0.1 -m "Release python-setup/pip v1.0.1: Fix cache key generation"
git push origin python-setup/pip/v1.0.1

# Move python-setup/pip/v1 to include the fix
git tag -fa python-setup/pip/v1 -m "Update python-setup/pip v1 to v1.0.1"
git push origin python-setup/pip/v1 --force

gh release create python-setup/pip/v1.0.1 \
  --title "python-setup/pip v1.0.1 - Bug Fixes" \
  --notes "Fix cache key generation for Windows"
```

#### Example 3: New Feature for Specific Action

```bash
# New feature release for mkdocs-deploy
git tag -a mkdocs-deploy/v1.1.0 -m "Release mkdocs-deploy v1.1.0: Add custom domain support"
git push origin mkdocs-deploy/v1.1.0

# Move mkdocs-deploy/v1 to include the feature
git tag -fa mkdocs-deploy/v1 -m "Update mkdocs-deploy v1 to v1.1.0"
git push origin mkdocs-deploy/v1 --force

gh release create mkdocs-deploy/v1.1.0 \
  --title "mkdocs-deploy v1.1.0 - Custom Domain Support" \
  --notes "## New Features

- Add support for custom domain configuration
- Improve deployment reliability"
```

#### Example 4: Breaking Change for Specific Action

```bash
# Breaking change release for python-setup/uv
git tag -a python-setup/uv/v2.0.0 -m "Release python-setup/uv v2.0.0: Remove deprecated inputs"
git push origin python-setup/uv/v2.0.0

# Create NEW major version tag (don't touch python-setup/uv/v1)
git tag -a python-setup/uv/v2 -m "Major version python-setup/uv v2"
git push origin python-setup/uv/v2

gh release create python-setup/uv/v2.0.0 \
  --title "python-setup/uv v2.0.0 - Breaking Changes" \
  --notes "## Breaking Changes

- Removed \`legacy-mode\` input
- Changed default behavior for lockfile validation

See migration guide in docs."
```

#### Example 5: Releasing Multiple Actions Independently

```bash
# Release python-setup/pip v1.0.1
git tag -a python-setup/pip/v1.0.1 -m "Release python-setup/pip v1.0.1"
git push origin python-setup/pip/v1.0.1
git tag -fa python-setup/pip/v1 -m "Update to v1.0.1"
git push origin python-setup/pip/v1 --force

# Release mkdocs-deploy v1.2.0 (different version, same commit)
git tag -a mkdocs-deploy/v1.2.0 -m "Release mkdocs-deploy v1.2.0"
git push origin mkdocs-deploy/v1.2.0
git tag -fa mkdocs-deploy/v1 -m "Update to v1.2.0"
git push origin mkdocs-deploy/v1 --force

# python-setup/uv can stay at its current version - not affected
```

## Best Practices

### For Maintainers

1. ✅ **Always use annotated tags** (`-a` flag) with meaningful messages
2. ✅ **Test thoroughly** before releasing
3. ✅ **Write clear release notes** explaining what changed
4. ✅ **Pin action dependencies** to specific SHA or version tags
5. ✅ **Document breaking changes** with migration guides
6. ✅ **Use deprecation warnings** before removing features
7. ✅ **Keep v1, v2, etc. updated** with each release (or namespaced equivalents)
8. ✅ **Never delete or force-push specific version tags** (only major versions)
9. ✅ **Choose a versioning strategy** (global or namespaced) and stick with it
10. ✅ **Use namespaced tags** when actions evolve independently
11. ✅ **Document your versioning strategy** in README for consumers

### For Consumers

1. ✅ **Use major version tags** for most workflows (`@v1` or `@action-name/v1`)
2. ✅ **Pin specific versions** for critical/production workflows (`@v1.0.0` or `@action-name/v1.0.0`)
3. ✅ **Read release notes** when major versions change
4. ✅ **Test in staging** before updating major versions
5. ✅ **Use Dependabot/Renovate** to track updates
6. ✅ **Never use `@main`** in production
7. ✅ **Understand the versioning strategy** used by the action maintainer

## Checklist for Releases

### Pre-Release

- [ ] All changes committed and pushed
- [ ] Tests passing
- [ ] Documentation updated
- [ ] CHANGELOG updated (if applicable)
- [ ] Version number decided (PATCH/MINOR/MAJOR)
- [ ] Breaking changes documented
- [ ] Migration guide written (if breaking changes)

### Release

- [ ] Create specific version tag (e.g., `v1.1.0`)
- [ ] Push specific version tag
- [ ] Move major version tag (e.g., `v1`)
- [ ] Force push major version tag
- [ ] Create GitHub release with notes
- [ ] Test the release in a sample workflow

### Post-Release

- [ ] Verify tags are correct on GitHub
- [ ] Verify release notes are clear
- [ ] Update README if needed
- [ ] Announce in relevant channels
- [ ] Monitor for issues

## References

- [Semantic Versioning](https://semver.org/)
- [GitHub Actions Versioning](https://github.com/actions/toolkit/blob/master/docs/action-versioning.md)
- [Git Tagging](https://git-scm.com/book/en/v2/Git-Basics-Tagging)

---

**Version**: 1.0  
**Last Updated**: January 2026  
**Maintained by**: serapeum-org

