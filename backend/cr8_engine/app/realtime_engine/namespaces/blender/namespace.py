"""
Blender Namespace Handler for Socket.IO
Handles all Blender client connections and events.
"""

import logging
import socketio
from typing import Dict
from .connection_handlers import ConnectionHandlersMixin
from .command_handlers import CommandHandlersMixin
from .registry_handlers import RegistryHandlersMixin


logger = logging.getLogger(__name__)


class BlenderNamespace(
    ConnectionHandlersMixin,
    CommandHandlersMixin,
    RegistryHandlersMixin,
    socketio.AsyncNamespace
):
    """Namespace handler for Blender clients."""

    def __init__(self, namespace: str = '/blender'):
        super().__init__(namespace)
        self.logger = logging.getLogger(__name__)
        # Store username to sid mapping for Blender clients
        self.username_to_sid: Dict[str, str] = {}

    @property
    def blaze_agent(self):
        """Get reference to shared BlazeAgent singleton (lazy initialization)."""
        from ..browser import get_shared_blaze_agent
        return get_shared_blaze_agent()
