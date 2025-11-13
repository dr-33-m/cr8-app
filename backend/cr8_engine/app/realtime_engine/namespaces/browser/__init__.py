"""
Browser Namespace Handler for Socket.IO
Handles all browser client connections and events.
"""

from .namespace import BrowserNamespace
from .singleton import initialize_shared_blaze_agent, get_shared_blaze_agent

__all__ = ['BrowserNamespace', 'initialize_shared_blaze_agent', 'get_shared_blaze_agent']
