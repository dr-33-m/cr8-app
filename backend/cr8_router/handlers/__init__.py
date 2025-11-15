"""
Handlers package for Blender AI Router
Contains all command handlers organized by functionality
"""

from .registry_handlers import (
    handle_get_available_addons,
    handle_get_addon_info,
    handle_refresh_addons
)

__all__ = [
    # Registry handlers
    'handle_get_available_addons',
    'handle_get_addon_info',
    'handle_refresh_addons',
]
