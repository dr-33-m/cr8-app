"""
Socket.IO event handlers for WebSocket communication.
Handles connection, disconnection, and message reception events.
"""

import logging
from ..message_types import MessageType
from .blender_handlers import execute_in_main_thread
from .command_handlers import process_message
from .registry_handlers import send_registry_update

logger = logging.getLogger(__name__)


def register_event_handlers(handler):
    """
    Register all Socket.IO event handlers on the handler instance.
    
    Args:
        handler: WebSocketHandler instance with sio client
    """
    
    @handler.sio.on('connect', namespace='/blender')
    def on_connect():
        logger.info("Connected to Socket.IO server")
        handler.processing_complete.clear()

        def send_init_message():
            try:
                # Send connection status via Socket.IO emit
                handler.sio.emit(
                    'connection_status',
                    {
                        'status': 'Connected',
                        'message': 'Blender registered'
                    },
                    namespace='/blender'
                )
                logger.info("Sent connection status to server")

                # Send registry update
                send_registry_update(handler.sio)
            except Exception as e:
                logger.error(f"Error in on_connect: {e}")

        execute_in_main_thread(send_init_message, ())

    @handler.sio.on('disconnect', namespace='/blender')
    def on_disconnect(reason):
        logger.info(f"Disconnected from server: {reason}")
        handler.processing_complete.set()
        handler.processing_commands.clear()

    @handler.sio.on('connect_error', namespace='/blender')
    def on_connect_error(data):
        logger.error(f"Connection error: {data}")

    @handler.sio.on(MessageType.COMMAND_RECEIVED, namespace='/blender')
    def on_command_received(data):
        """Handle commands forwarded from backend (standardized)"""
        logger.info(f"Received {MessageType.COMMAND_RECEIVED}: {data}")

        def execute():
            process_message(data, handler)

        execute_in_main_thread(execute, ())

    @handler.sio.on('ping', namespace='/blender')
    def on_ping(data):
        """Handle ping events"""
        logger.info(f"Received ping: {data}")

        def execute():
            from .utility_handlers import handle_ping
            handle_ping(data, handler)

        execute_in_main_thread(execute, ())
