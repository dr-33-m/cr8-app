"""
Socket.IO Namespaces for cr8_engine.
Provides separate namespaces for browser and Blender clients.
"""

from .browser import BrowserNamespace
from .blender import BlenderNamespace

__all__ = [
    'BrowserNamespace',
    'BlenderNamespace',
]
