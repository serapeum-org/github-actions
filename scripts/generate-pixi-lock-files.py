"""
Generate lock files for existing pyproject.toml files in tests/data/pixi/.
"""

import shutil
import subprocess
import sys
from pathlib import Path

# Force UTF-8 encoding for Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

PIXI_TEST_DATA = "tests/data/pixi"


def find_pyproject_files(base_dir):
    """Find all pyproject.toml files in the test fixtures directory."""
    fixtures_dir = base_dir / PIXI_TEST_DATA

    if not fixtures_dir.exists():
        print(f"❌ Test fixtures directory not found: {fixtures_dir}")
        return []

    pyproject_files = list(fixtures_dir.glob("*/pyproject.toml"))
    return pyproject_files


def generate_lock_files(pyproject_files):
    """Generate lock files for each pyproject.toml file."""
    if not pyproject_files:
        print("❌ No pyproject.toml files found")
        return False

    print(f"✨ Found {len(pyproject_files)} pyproject.toml files\n")

    success_count = 0
    failed_count = 0

    for toml_file in pyproject_files:
        test_dir = toml_file.parent
        test_name = test_dir.name

        print(f"📝 Processing {test_name}...")
        print(f"   Location: {toml_file}")

        # Check if lock file already exists
        lock_file = test_dir / "pixi.lock"
        if lock_file.exists():
            print(f"   ⚠️  Lock file already exists, regenerating...")
            lock_file.unlink()

        # Generate lock file using pixi
        print(f"   🔒 Generating lock file...")
        try:
            result = subprocess.run(
                ["pixi", "install"],
                cwd=test_dir,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                print(f"   ✅ Lock file generated successfully\n")
                success_count += 1
            else:
                print(f"   ❌ Failed to generate lock file")
                print(f"   Error: {result.stderr}\n")
                failed_count += 1

        except subprocess.TimeoutExpired:
            print(f"   ⏱️  Timeout generating lock file\n")
            failed_count += 1
        except FileNotFoundError:
            print(f"   ❌ pixi command not found. Please install pixi first.")
            print(f"      Visit: https://pixi.sh\n")
            return False

    return success_count, failed_count


def cleanup_pixi_environments(pyproject_files):
    """Delete .pixi environment folders after lock files are generated."""
    print("\n🧹 Cleaning up .pixi environment folders...\n")

    cleaned_count = 0
    failed_count = 0

    for toml_file in pyproject_files:
        test_dir = toml_file.parent
        test_name = test_dir.name
        pixi_dir = test_dir / ".pixi"

        if pixi_dir.exists():
            try:
                shutil.rmtree(pixi_dir)
                print(f"   ✅ Deleted .pixi folder for {test_name}")
                cleaned_count += 1
            except Exception as e:
                print(f"   ❌ Failed to delete .pixi folder for {test_name}: {e}")
                failed_count += 1
        else:
            print(f"   ⏭️  No .pixi folder found for {test_name}")

    print(f"\n   Cleaned: {cleaned_count}, Failed: {failed_count}\n")
    return cleaned_count, failed_count


def main():
    # Get the repository root
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent

    print(f"🔍 Searching for pyproject.toml files in {PIXI_TEST_DATA}/...\n")

    pyproject_files = find_pyproject_files(repo_root)

    if not pyproject_files:
        print("❌ No pyproject.toml files found to process")
        sys.exit(1)

    result = generate_lock_files(pyproject_files)

    if result is False:
        print("\n❌ Lock file generation aborted")
        sys.exit(1)

    success_count, failed_count = result

    # Clean up .pixi environment folders if lock files were generated successfully
    if success_count > 0:
        cleanup_pixi_environments(pyproject_files)

    print("=" * 60)
    print(f"✅ Lock file generation complete!")
    print(f"   Success: {success_count}")
    print(f"   Failed: {failed_count}")
    print("=" * 60)

    if failed_count > 0:
        print("\n⚠️  Some lock files failed to generate")
        sys.exit(1)

if __name__ == "__main__":
    main()
