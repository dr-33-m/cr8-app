"""
Blender AI Router - Main AI orchestration addon for Blender
Discovers and routes commands to AI-capable addons
"""

import bpy
import logging
from pathlib import Path
from .registry import AIAddonRegistry, AICommandRouter
from .handlers import registry_handlers

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bl_info = {
    "name": "Blender AI Router",
    "author": "Cr8-xyz <thamsanqa.dev@gmail.com>",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Tools",
    "description": "Main AI router for discovering and routing commands to AI-capable addons",
    "warning": "",
    "wiki_url": "https://code.cr8-xyz.art/Cr8-xyz/cr8-app",
    "category": "Development",
}

# Global instances
_registry = None
_router = None


def get_registry():
    """Get the global addon registry instance"""
    global _registry
    if _registry is None:
        _registry = AIAddonRegistry()
    return _registry


def get_router():
    """Get the global command router instance"""
    global _router
    if _router is None:
        _router = AICommandRouter(get_registry())
    return _router


# Import all command handlers from their respective modules
from .handlers.registry_handlers import (
    handle_get_available_addons,
    handle_get_addon_info,
    handle_refresh_addons
)

# Export all command handlers for the router addon itself
AI_COMMAND_HANDLERS = {
    'get_available_addons': handle_get_available_addons,
    'get_addon_info': handle_get_addon_info,
    'refresh_addons': handle_refresh_addons,
}


def register():
    """Register the AI router addon"""
    try:
        logger.info("Registering Blender AI Router...")

        # Register WebSocket system
        from . import ws
        ws.register()

        # Initialize registry and router
        registry = get_registry()
        router = get_router()

        logger.info(
            f"AI Router registered with {len(registry.get_registered_addons())} addons")

    except Exception as e:
        logger.error(f"Failed to register AI Router: {str(e)}")
        raise


def unregister():
    """Unregister the AI router addon"""
    try:
        logger.info("Unregistering Blender AI Router...")

        # Unregister WebSocket system
        from . import ws
        ws.unregister()

        # Clear global instances
        global _registry, _router
        _registry = None
        _router = None

        logger.info("AI Router unregistered")

    except Exception as e:
        logger.error(f"Failed to unregister AI Router: {str(e)}")


if __name__ == "__main__":
    register()
