"""
Response manager for sending Socket.IO responses.
Refactored to use standardized message structure (Phase 3)
"""

import logging
import json
import uuid

logger = logging.getLogger(__name__)


def generate_message_id() -> str:
    """Generate unique message ID"""
    return str(uuid.uuid4())


class ResponseManager:
    """
    Singleton class for managing Socket.IO responses.
    Provides a centralized way to send responses without dependency on WebSocketHandler.
    """
    _instance = None
    _socketio_client = None

    def __new__(cls):
        if cls._instance is None:
            logger.info("Creating new ResponseManager instance")
            cls._instance = super(ResponseManager, cls).__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls):
        """Get the singleton instance of ResponseManager"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def set_socketio(self, sio):
        """Set the Socket.IO client to use for sending responses"""
        logger.info("Setting Socket.IO client in ResponseManager")
        self._socketio_client = sio

    def send_response(self, command, result, data=None, message_id=None, route='direct'):
        """
        Send a standardized Socket.IO response.

        :param command: The command name
        :param result: Boolean indicating success or failure
        :param data: Optional additional data to send
        :param message_id: Message ID for tracking (REQUIRED)
        :param route: Route type ('direct' or 'agent') to preserve from original command
        """
        if not self._socketio_client:
            logger.error("Cannot send response: Socket.IO client not set")
            return False

        # Enforce message_id requirement
        if message_id is None:
            message_id = generate_message_id()
            logger.warning(f"No message_id provided, generated: {message_id}")

        logger.info(f"Preparing standardized response for command: {command} with route: {route}")
        
        # Create standardized response structure
        status = 'success' if result else 'error'
        
        # Build standardized message
        response = {
            'message_id': message_id,
            'type': 'command_completed' if result else 'command_failed',
            'payload': {
                'status': status,
                'data': data if data is not None else {'command': command}
            },
            'metadata': {
                'timestamp': __import__('time').time(),
                'source': 'blender',
                'route': route  # Preserve the route from original command
            }
        }

        logger.info(f"Sending standardized Socket.IO response: {response}")

        # Send the response via Socket.IO emit
        try:
            # Use the new event name based on success/failure
            event_name = 'command_completed' if result else 'command_failed'
            
            self._socketio_client.emit(
                event_name,
                response,
                namespace='/blender'
            )
            logger.info(f"Successfully emitted {event_name} for command: {command}")
            return True
        except Exception as e:
            logger.error(f"Error sending Socket.IO response: {e}")
            return False
