"""
Real-time Engine Package Initialization

This module exposes Socket.IO server components for real-time communication.
"""

# Import Socket.IO server components
from .socketio_server import create_socketio_server, create_socketio_app
from .namespaces import BrowserNamespace, BlenderNamespace

# Optional: Define what should be imported with *
__all__ = [
    'create_socketio_server',
    'create_socketio_app',
    'BrowserNamespace',
    'BlenderNamespace',
]

# Package version
__version__ = '2.0.0'
