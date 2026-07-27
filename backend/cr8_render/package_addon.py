#!/usr/bin/env python3
"""
Cr8 Render Addon Packaging Script
=============================================

This script packages the Cr8 Render addon for distribution.
Creates a ZIP file that can be installed directly in Blender.
Image rendering and cloud output addon.

DYNAMIC PACKAGING: Automatically discovers all addon files and directories.
No manual file lists needed - just add new modules and they're included!
"""

import os
import re
import zipfile
import shutil
from pathlib import Path
import argparse
import fnmatch


def read_manifest_meta():
    """
    Read id and version from blender_manifest.toml — the single source of truth.

    The zip's internal root directory MUST equal the extension id, or Blender
    installs the addon under a module path that nothing else can import, and the
    filename should carry the real version. Hardcoding either lets the shipped
    zip drift from the manifest, which stays invisible until runtime.
    """
    text = Path("blender_manifest.toml").read_text()
    id_match = re.search(r'^id\s*=\s*"([^"]+)"', text, re.MULTILINE)
    version_match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not id_match or not version_match:
        raise SystemExit(
            "ERROR: could not read id/version from blender_manifest.toml")
    return id_match.group(1), version_match.group(1)


def should_exclude(path, exclude_patterns):
    """Check if a path matches any exclude pattern"""
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(os.path.basename(path), pattern):
            return True
    return False


def discover_addon_files(exclude_patterns):
    """
    Dynamically discover all addon files and directories.
    Returns a tuple of (files, directories) to include in the package.
    """
    addon_files = []
    addon_directories = []

    # Scan current directory for addon files
    for item in os.listdir('.'):
        if os.path.isfile(item):
            # Every root-level Python module, plus the manifests — NOT a fixed
            # whitelist. The other addons' scripts name their four files
            # explicitly, which silently drops any new root module from the zip
            # and surfaces as an ImportError at addon load rather than a
            # packaging error. Growth here is expected (video, colour, output
            # formats), so discovery has to cover it.
            is_manifest = item in (
                'blender_manifest.toml', 'addon_ai.json', 'README.md')
            is_module = item.endswith('.py') and item != 'package_addon.py'
            if (is_manifest or is_module) and not should_exclude(item, exclude_patterns):
                addon_files.append(item)
        elif os.path.isdir(item):
            # Include directories that contain Python modules
            if not should_exclude(item, exclude_patterns):
                # Check if directory has Python files
                has_python_files = False
                for root, dirs, files in os.walk(item):
                    # Skip excluded directories
                    dirs[:] = [d for d in dirs if not should_exclude(d, exclude_patterns)]
                    
                    for file in files:
                        if file.endswith('.py') and not should_exclude(file, exclude_patterns):
                            has_python_files = True
                            break
                    if has_python_files:
                        break
                
                if has_python_files:
                    addon_directories.append(item)

    return addon_files, addon_directories


def add_directory_to_zip(zf, directory, base_arcname, exclude_patterns):
    """Recursively add directory contents to ZIP file"""
    for root, dirs, files in os.walk(directory):
        # Remove excluded directories
        dirs[:] = [d for d in dirs if not should_exclude(d, exclude_patterns)]

        for file in files:
            if should_exclude(file, exclude_patterns):
                continue

            file_path = os.path.join(root, file)
            # Create archive path relative to base
            rel_path = os.path.relpath(file_path, directory)
            arcname = f"{base_arcname}/{directory}/{rel_path}".replace('\\', '/')
            zf.write(file_path, arcname)
            print(f"  Added: {file_path}")


def create_addon_package(output_dir="dist", version=None):
    """Create a ZIP package of the addon for distribution"""

    # Define patterns to exclude from package
    exclude_patterns = [
        "package_addon.py",
        "__pycache__",
        ".git*",
        ".gitignore",
        "*.pyc",
        "*.pyo",
        ".pytest_cache",
        "test_*",
        "*_test.py",
        ".env*",
        "dist",
        "build",
        "*.egg-info"
    ]

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Determine version for filename
    # id and version both come from blender_manifest.toml; --version overrides
    # only the filename, for one-off builds.
    addon_id, manifest_version = read_manifest_meta()
    version = version or manifest_version

    # Create package filename
    package_name = f"{addon_id}_v{version}.zip"
    package_path = output_path / package_name

    print(f"Creating addon package: {package_path}")
    print(f"🔍 Discovering addon files dynamically...")

    # Dynamically discover addon files and directories
    addon_files, addon_directories = discover_addon_files(exclude_patterns)

    if not addon_files or not addon_directories:
        print("❌ No addon files or directories found!")
        return None

    print(f"✓ Found {len(addon_files)} addon files")
    print(f"✓ Found {len(addon_directories)} addon directories")

    # Create ZIP package
    with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add individual files
        for file_name in addon_files:
            if os.path.exists(file_name):
                # Add file to ZIP with addon folder structure
                arcname = f"{addon_id}/{file_name}"
                zf.write(file_name, arcname)
                print(f"  Added: {file_name}")
            else:
                print(f"  WARNING: Missing file: {file_name}")

        # Add directories
        for directory in addon_directories:
            if os.path.exists(directory) and os.path.isdir(directory):
                print(f"  Adding directory: {directory}/")
                add_directory_to_zip(zf, directory, addon_id, exclude_patterns)
            else:
                print(f"  WARNING: Missing directory: {directory}")

    print(f"\n✅ Package created successfully: {package_path}")
    print(f"📦 Package size: {package_path.stat().st_size / 1024:.1f} KB")

    # Validate package
    print("\n🔍 Validating package contents:")
    with zipfile.ZipFile(package_path, 'r') as zf:
        files_in_zip = zf.namelist()
        for file_name in files_in_zip:
            print(f"  ✓ {file_name}")

    print(f"\n📋 Installation Instructions:")
    print(f"1. Open Blender")
    print(f"2. Go to Edit → Preferences → Add-ons")
    print(f"3. Click 'Install...' and select: {package_name}")
    print(f"4. Enable 'Cr8 Render' in the addon list")
    print(f"5. Ensure Blaze Router (cr8_router) is also installed — it discovers this addon")
    print(f"6. The router will pick up render_image from addon_ai.json automatically")

    return package_path


def create_development_package():
    """Create a development package with all source files"""
    exclude_patterns = [
        "package_addon.py",
        "__pycache__",
        ".git*",
        ".gitignore",
        "*.pyc",
        "*.pyo",
        ".pytest_cache",
        "test_*",
        "*_test.py",
        ".env*",
        "dist",
        "build",
        "*.egg-info"
    ]

    output_path = Path("dist")
    output_path.mkdir(exist_ok=True)

    addon_id, _ = read_manifest_meta()
    package_name = f"{addon_id}_dev.zip"
    package_path = output_path / package_name

    print(f"Creating development package: {package_path}")
    print(f"🔍 Discovering addon files dynamically...")

    # Dynamically discover addon files and directories
    addon_files, addon_directories = discover_addon_files(exclude_patterns)

    print(f"✓ Found {len(addon_files)} addon files")
    print(f"✓ Found {len(addon_directories)} addon directories")

    with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_name in addon_files:
            if os.path.exists(file_name):
                arcname = f"{addon_id}/{file_name}"
                zf.write(file_name, arcname)
                print(f"  Added: {file_name}")

        # Add directories
        for directory in addon_directories:
            if os.path.exists(directory) and os.path.isdir(directory):
                print(f"  Adding directory: {directory}/")
                add_directory_to_zip(zf, directory, addon_id, exclude_patterns)

    print(f"✅ Development package created: {package_path}")
    return package_path


def validate_addon_structure():
    """
    Validate that addon structure is valid.
    Uses dynamic discovery - no hardcoded file lists!
    """
    # Essential files that must exist
    essential_files = [
        "__init__.py",
        "blender_manifest.toml",
        "addon_ai.json"
    ]

    # Exclude patterns
    exclude_patterns = [
        "package_addon.py",
        "__pycache__",
        ".git*",
        "*.pyc",
        "test_*",
        "*_test.py"
    ]

    missing_files = []
    for file_name in essential_files:
        if not os.path.exists(file_name):
            missing_files.append(file_name)

    if missing_files:
        print("❌ Missing required files:")
        for file_name in missing_files:
            print(f"  - {file_name}")
        return False

    # Check that we have at least one Python module directory
    addon_files, addon_directories = discover_addon_files(exclude_patterns)

    if not addon_directories:
        print("❌ No Python module directories found!")
        print("   Expected directories with .py files (e.g., registry/, ws/, handlers/)")
        return False

    print("✅ All required files present")
    print(f"✅ Found {len(addon_directories)} addon module directories:")
    for directory in addon_directories:
        print(f"   - {directory}/")
    print(f"✅ Found {len(addon_files)} addon files:")
    for file_name in addon_files:
        print(f"   - {file_name}")
    print("✅ Addon structure is valid and ready to package!")
    return True


def show_addon_info():
    """Display information about the addon"""
    print("🎯 Cr8 Render")
    print("=" * 40)
    print("Main AI router addon for discovering and routing commands to AI-capable addons")
    print()
    print("📋 Features:")
    print("  • AI command routing and discovery")
    print("  • Multi-addon orchestration")
    print("  • WebSocket integration with CR8 Engine")
    print("  • Automatic addon discovery and registration")
    print("  • Animation and viewport controls")
    print("  • Natural language command processing")
    print("  • Modular registry architecture (manifest/ and discovery/ subdirectories)")
    print()
    print("🔧 Prerequisite Addons:")
    print("  • Blaze Router (cr8_router)")
    print("  • Repository: https://code.cr8-xyz.art/Cr8-xyz/set-builder")
    print()
    print("📦 Packaging:")
    print("  • Dynamic file discovery - add new modules without updating the script!")
    print("  • Automatic exclusion of build artifacts and cache files")
    print("  • Supports nested directory structures")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Package Cr8 Render addon (with dynamic file discovery)")
    parser.add_argument(
        "--version", help="Version string for package filename")
    parser.add_argument("--dev", action="store_true",
                        help="Create development package with all source files")
    parser.add_argument("--output", default="dist", help="Output directory")
    parser.add_argument("--validate", action="store_true",
                        help="Only validate addon structure")
    parser.add_argument("--info", action="store_true",
                        help="Show addon information")

    args = parser.parse_args()

    if args.info:
        show_addon_info()
        return

    if args.validate:
        print("🔍 Validating addon structure...")
        if validate_addon_structure():
            print("✅ Addon structure is valid")
        else:
            print("❌ Addon structure validation failed")
        return

    print("🚀 Cr8 Render Packager")
    print("=" * 40)
    print("📝 Using DYNAMIC file discovery - no hardcoded file lists!")
    print()

    # Validate before packaging
    if not validate_addon_structure():
        print("❌ Cannot package addon - structure validation failed")
        return

    if args.dev:
        create_development_package()
    else:
        create_addon_package(args.output, args.version)

    print("\n🎉 Packaging complete!")
    print("\n💡 Next steps:")
    print("  1. Install the addon in Blender")
    print("  2. Ensure Blaze Router (cr8_router) is also installed")
    print("  3. Enable both addons in Blender preferences")
    print("  4. Test a render via the workspace actions menu")
    print()
    print("💡 Pro tip: Add new modules to the addon without updating this script!")
    print("   The packager will automatically discover and include them.")


if __name__ == "__main__":
    main()
