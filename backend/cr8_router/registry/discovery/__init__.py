"""
Discovery and loading module for AI addon discovery and handler loading.
Provides addon scanning and handler loading functionality.
"""

from .scanner import (
    get_addon_paths,
    scan_directory,
    discover_addons,
)
from .handler_loader import load_addon_handlers

__all__ = [
    'get_addon_paths',
    'scan_directory',
    'discover_addons',
    'load_addon_handlers',
]
