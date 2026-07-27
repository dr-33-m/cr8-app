#!/usr/bin/env python3
"""
Blender Controls Addon Packaging Script
=======================================

This script packages the Blender Controls addon for distribution.
Creates a ZIP file that can be installed directly in Blender.
Provides comprehensive scene manipulation and viewport control capabilities for AI agents.
"""

import os
import re
import zipfile
import shutil
from pathlib import Path
import argparse


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


def add_directory_to_zip(zf, directory, base_arcname, exclude_files):
    """Recursively add directory contents to ZIP file"""
    for root, dirs, files in os.walk(directory):
        # Remove excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_files]

        for file in files:
            if file.endswith('.pyc') or file in exclude_files:
                continue

            file_path = os.path.join(root, file)
            # Create archive path relative to base
            rel_path = os.path.relpath(file_path, directory)
            arcname = f"{base_arcname}/{directory}/{rel_path}".replace(
                '\\', '/')
            zf.write(file_path, arcname)
            print(f"  Added: {file_path}")


def create_addon_package(output_dir="dist", version=None):
    """Create a ZIP package of the addon for distribution"""

    # Define addon files to include
    addon_files = [
        "__init__.py",
        "blender_manifest.toml",
        "addon_ai.json",
        "README.md"
    ]

    # Define directories to include
    addon_directories = [
        "handlers",
        "utils"
    ]

    # Files to exclude from package
    exclude_files = [
        "package_addon.py",
        "__pycache__",
        ".git",
        ".gitignore",
        "*.pyc"
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
                add_directory_to_zip(
                    zf, directory, addon_id, exclude_files)
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
    print(f"4. Enable 'Blaze Controls' in the addon list")
    print(f"5. Ensure Blender AI Router (cr8-router) is also installed as prerequisite")
    print(f"6. The Controls addon will provide scene manipulation capabilities to AI agents")

    return package_path


def create_development_package():
    """Create a development package with all source files"""
    addon_files = [
        "__init__.py",
        "blender_manifest.toml",
        "addon_ai.json",
        "README.md",
        "package_addon.py"  # Include packaging script in dev build
    ]

    addon_directories = [
        "handlers",
        "utils"
    ]

    output_path = Path("dist")
    output_path.mkdir(exist_ok=True)

    addon_id, _ = read_manifest_meta()
    package_name = f"{addon_id}_dev.zip"
    package_path = output_path / package_name

    print(f"Creating development package: {package_path}")

    with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_name in addon_files:
            if os.path.exists(file_name):
                arcname = f"{addon_id}/{file_name}"
                zf.write(file_name, arcname)
                print(f"  Added: {file_name}")

        # Add directories
        exclude_files = ["package_addon.py", "__pycache__", ".git", "*.pyc"]
        for directory in addon_directories:
            if os.path.exists(directory) and os.path.isdir(directory):
                print(f"  Adding directory: {directory}/")
                add_directory_to_zip(
                    zf, directory, addon_id, exclude_files)

    print(f"✅ Development package created: {package_path}")
    return package_path


def validate_addon_structure():
    """Validate that all required files are present"""
    required_files = [
        "__init__.py",
        "blender_manifest.toml",
        "addon_ai.json"
    ]

    required_directories = [
        "handlers",
        "utils"
    ]

    missing_files = []
    for file_name in required_files:
        if not os.path.exists(file_name):
            missing_files.append(file_name)

    missing_directories = []
    for dir_name in required_directories:
        if not os.path.exists(dir_name) or not os.path.isdir(dir_name):
            missing_directories.append(dir_name)

    if missing_files:
        print("❌ Missing required files:")
        for file_name in missing_files:
            print(f"  - {file_name}")

    if missing_directories:
        print("❌ Missing required directories:")
        for dir_name in missing_directories:
            print(f"  - {dir_name}/")

    if missing_files or missing_directories:
        return False

    print("✅ All required files and directories present")
    return True


def show_addon_info():
    """Display information about the addon"""
    print("🎯 Blender Controls")
    print("=" * 40)
    print("Scene manipulation and viewport control capabilities for AI agents")
    print()
    print("📋 Features:")
    print("  • Animation playback controls (play, pause, timeline navigation)")
    print("  • Viewport shading modes (solid, rendered)")
    print("  • 3D navigation controls (orbit, pan, zoom)")
    print("  • Screenshot capture with visual analysis")
    print("  • Keyframe navigation and jumping")
    print("  • Immediate visual feedback in Blender viewport")
    print()
    print("🔧 Prerequisite Addons:")
    print("  • Blender AI Router (cr8-router)")
    print("  • Repository: https://code.cr8-xyz.art/Cr8-xyz/cr8-app")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Package Blender Controls addon")
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

    print("🚀 Blender Controls Packager")
    print("=" * 40)

    # Validate before packaging
    if not validate_addon_structure():
        print("❌ Cannot package addon - missing required files")
        return

    if args.dev:
        create_development_package()
    else:
        create_addon_package(args.output, args.version)

    print("\n🎉 Packaging complete!")
    print("\n💡 Next steps:")
    print("  1. Install the addon in Blender")
    print("  2. Ensure Blender AI Router (cr8-router) is also installed")
    print("  3. Enable both addons in Blender preferences")
    print("  4. Test scene manipulation and viewport control functionality")


if __name__ == "__main__":
    main()
