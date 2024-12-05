"""
WebSocket Server Package Initialization

This module exposes key classes and functions from the package,
making them easy to import.
"""

# Import key classes to make them accessible at the package level
from .connection_manager import WebSocketConnectionManager
from .ws_server import WebSocketServer

# Optional: Define what should be imported with *
__all__ = [
    'WebSocketConnectionManager',
    'WebSocketServer'
]

# Optional: Package-level version information
__version__ = '0.1.0'
