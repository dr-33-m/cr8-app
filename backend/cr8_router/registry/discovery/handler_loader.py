"""
Handler loading from AI addon modules.
Handles importing addon modules and extracting command handlers.
"""

import logging
import importlib
from pathlib import Path
import bpy

logger = logging.getLogger(__name__)


def load_addon_handlers(addon_id: str, manifest) -> dict:
    """
    Load command handlers from the addon's Python module.
    
    Args:
        addon_id: ID of the addon
        manifest: AddonManifest object containing addon info
        
    Returns:
        Dictionary of handlers if found, empty dict otherwise
    """
    try:
        # Get the base addon name from path
        base_addon_name = manifest.addon_path.name

        # Find the correct import name from enabled addons
        correct_import_name = _get_correct_import_name(base_addon_name)

        if not correct_import_name:
            logger.warning(
                f"Addon {addon_id} ({base_addon_name}) is not enabled in Blender"
            )
            return {}

        # Import the addon module using correct import name
        addon_module = importlib.import_module(correct_import_name)

        # Look for AI_COMMAND_HANDLERS export
        if hasattr(addon_module, 'AI_COMMAND_HANDLERS'):
            handlers = addon_module.AI_COMMAND_HANDLERS
            if isinstance(handlers, dict):
                logger.info(
                    f"Loaded {len(handlers)} handlers for addon {addon_id}"
                )
                return handlers
            else:
                logger.error(
                    f"AI_COMMAND_HANDLERS must be a dict in addon {addon_id}"
                )
                return {}
        else:
            logger.warning(
                f"No AI_COMMAND_HANDLERS found in addon {addon_id}"
            )
            return {}

    except ImportError as e:
        logger.error(f"Failed to import addon {addon_id}: {str(e)}")
        return {}
    except Exception as e:
        logger.error(
            f"Error loading handlers for addon {addon_id}: {str(e)}"
        )
        return {}


def _get_correct_import_name(base_addon_name: str) -> str:
    """
    Resolve the correct import name for an addon.
    
    Extensions use bl_ext.* prefix, traditional addons use base name.
    
    Args:
        base_addon_name: Base name of the addon directory
        
    Returns:
        Correct import name if found, None otherwise
    """
    try:
        enabled_addons = list(bpy.context.preferences.addons.keys())

        for addon_name in enabled_addons:
            if addon_name.endswith(base_addon_name):
                return addon_name

        return None

    except Exception as e:
        logger.error(f"Error resolving import name for {base_addon_name}: {str(e)}")
        return None
