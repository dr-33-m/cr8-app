"""
Socket.IO Namespaces for cr8_engine.
Provides separate namespaces for browser and Blender clients.
"""

from .browser_namespace import BrowserNamespace
from .blender_namespace import BlenderNamespace

__all__ = [
    'BrowserNamespace',
    'BlenderNamespace',
]
