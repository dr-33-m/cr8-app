"""BrowserNamespace - Main namespace for browser connections."""

import logging
import socketio
from typing import Dict

from .connection_handlers import ConnectionHandlersMixin
from .session_handlers import SessionHandlersMixin
from .command_handlers import CommandHandlersMixin
from .notification_handlers import NotificationHandlersMixin
from .singleton import get_shared_blaze_agent


class BrowserNamespace(
    ConnectionHandlersMixin,
    SessionHandlersMixin,
    CommandHandlersMixin,
    NotificationHandlersMixin,
    socketio.AsyncNamespace,
):
    """Namespace handler for browser clients."""
    
    def __init__(self, namespace: str = '/browser'):
        super().__init__(namespace)
        self.logger = logging.getLogger(__name__)
        # Store username to sid mapping for finding sessions
        self.username_to_sid: Dict[str, str] = {}
    
    @property
    def blaze_agent(self):
        """Get reference to shared BlazeAgent singleton (lazy initialization)."""
        return get_shared_blaze_agent()
