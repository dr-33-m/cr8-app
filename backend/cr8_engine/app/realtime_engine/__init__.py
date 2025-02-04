"""
WebSocket Server Package Initialization

This module exposes key classes and functions from the package,
making them easy to import.
"""

# Import key classes to make them accessible at the package level
from .websockets.session_manager import SessionManager
from .websockets.websocket_handler import WebSocketHandler

# Optional: Define what should be imported with *
__all__ = [
    'SessionManager',
    'WebSocketHandler',
]

# Optional: Package-level version information
__version__ = '0.1.0'
