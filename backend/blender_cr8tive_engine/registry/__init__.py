"""
Registry module for the Blender AI Router
Handles addon discovery, validation, and management
"""

from .addon_registry import AIAddonRegistry
from .command_router import AICommandRouter

__all__ = ['AIAddonRegistry', 'AICommandRouter']
