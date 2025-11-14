"""
Utility functions and singletons for WebSocket communication.
"""

from .response_manager import ResponseManager
from .session_manager import SessionManager

# Initialize singleton instances
response_manager = ResponseManager.get_instance()
session_manager = SessionManager.get_instance()

__all__ = [
    'ResponseManager',
    'SessionManager',
    'response_manager',
    'session_manager'
]
