"""
Response manager for sending WebSocket responses.
"""

import logging
import json

logger = logging.getLogger(__name__)


class ResponseManager:
    """
    Singleton class for managing WebSocket responses.
    Provides a centralized way to send responses without dependency on WebSocketHandler.
    """
    _instance = None
    _websocket = None

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

    def set_websocket(self, websocket):
        """Set the WebSocket connection to use for sending responses"""
        logger.info("Setting WebSocket connection in ResponseManager")
        self._websocket = websocket

    def send_response(self, command, result, data=None, message_id=None):
        """
        Send a WebSocket response.

        :param command: The command to send (e.g., 'template_controls')
        :param result: Boolean indicating success or failure
        :param data: Optional additional data to send (e.g., controllables object)
        :param message_id: Optional message ID for tracking requests
        """
        if not self._websocket:
            logger.error("Cannot send response: WebSocket not set")
            return False

        logger.info(f"Preparing response for command: {command}")
        status = 'success' if result else 'failed'

        response = {
            'command': command,
            'status': status
        }

        # CRITICAL FIX: Include message_id at top level if provided
        # This is required for FastAPI to correlate responses back to B.L.A.Z.E
        if message_id is not None:
            response['message_id'] = message_id
            logger.info(f"Including message_id in response: {message_id}")

        # Include the data in the response if provided
        if data is not None:
            response['data'] = data

        # Convert the response dictionary to a JSON string
        json_response = json.dumps(response)
        logger.info(f"Sending WebSocket response: {json_response}")

        # Send the response via WebSocket
        try:
            self._websocket.send(json_response)
            return True
        except Exception as e:
            logger.error(f"Error sending WebSocket response: {e}")
            return False
