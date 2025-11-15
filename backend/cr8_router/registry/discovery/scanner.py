"""
Addon discovery and scanning for AI-capable addons.
Handles finding addons in Blender's addon directories (both traditional and extensions).
"""

import logging
from pathlib import Path
import bpy

logger = logging.getLogger(__name__)


def get_addon_paths() -> list:
    """
    Get all possible addon paths in Blender (both traditional addons and extensions).
    
    Returns:
        List of Path objects pointing to addon directories
    """
    addon_paths = []

    # Traditional addon directories
    # User addons directory
    if hasattr(bpy.utils, 'user_script_path'):
        user_scripts = bpy.utils.user_script_path()
        if user_scripts:
            addon_paths.append(Path(user_scripts) / "addons")

    # System addons directories
    for path in bpy.utils.script_paths():
        addon_paths.append(Path(path) / "addons")

    # Extensions directories (Blender 4.2+)
    config_path = bpy.utils.user_resource('CONFIG')
    if config_path:
        # Go up one level from /config to get base Blender directory
        blender_base = Path(config_path).parent
        # Add extensions paths
        addon_paths.append(blender_base / "extensions" / "user_default")
        addon_paths.append(blender_base / "extensions" / "blender_org")

    return addon_paths


def scan_directory(directory: Path, manifest_loader) -> list:
    """
    Scan a directory for AI-capable addons.
    
    Args:
        directory: Path to directory to scan
        manifest_loader: Function to load and parse manifest files
        
    Returns:
        List of AddonManifest objects found in directory
    """
    discovered = []

    if not directory.exists() or not directory.is_dir():
        logger.warning(f"Directory does not exist or is not a directory: {directory}")
        return discovered

    try:
        for item in directory.iterdir():
            if item.is_dir():
                manifest_path = item / "addon_ai.json"
                if manifest_path.exists():
                    try:
                        manifest = manifest_loader(item, manifest_path)
                        if manifest and manifest.is_valid:
                            discovered.append(manifest)
                    except Exception as e:
                        logger.error(
                            f"Error loading manifest from {item}: {str(e)}"
                        )
    except Exception as e:
        logger.error(f"Error scanning directory {directory}: {str(e)}")

    return discovered


def discover_addons(manifest_loader) -> list:
    """
    Main discovery orchestration - find all AI-capable addons.
    
    Args:
        manifest_loader: Function to load and parse manifest files
        
    Returns:
        List of all discovered AddonManifest objects
    """
    logger.info("Scanning for AI-capable addons...")

    discovered_addons = []

    # Get Blender's addons directories
    addon_paths = get_addon_paths()

    for addon_path in addon_paths:
        discovered_addons.extend(scan_directory(addon_path, manifest_loader))

    logger.info(f"Discovered {len(discovered_addons)} AI-capable addons")
    return discovered_addons
