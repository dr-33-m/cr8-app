"""
Utility handlers for WebSocket communication.
Handles ping, connection confirmation, and other utility operations.
"""

import logging
from ..utils.response_manager import ResponseManager

logger = logging.getLogger(__name__)


def handle_ping(data, handler):
    """
    Handle ping command by responding with a pong.
    
    Args:
        data: Ping data from Socket.IO
        handler: WebSocketHandler instance
    """
    message_id = data.get('message_id')
    response_manager = ResponseManager.get_instance()
    response_manager.send_response(
        "ping_result", True, {"pong": True}, message_id)
    logger.info(f"Responded to ping with message_id: {message_id}")


def handle_connection_confirmation(data, handler):
    """
    Handle connection confirmation from CR8 Engine.
    
    Args:
        data: Connection confirmation data from Socket.IO
        handler: WebSocketHandler instance
    """
    message_id = data.get('message_id')
    status = data.get('status')
    message = data.get('message')
    logger.info(
        f"Received connection confirmation: status={status}, message={message}")

    # Send registry update to FastAPI when connection is confirmed
    from .registry_handlers import send_registry_update
    send_registry_update(handler.sio)

    # No need to respond, just acknowledge receipt
    if message_id:
        response_manager = ResponseManager.get_instance()
        response_manager.send_response(
            "connection_confirmation_result", True, {"acknowledged": True}, message_id)
        logger.info(
            f"Acknowledged connection confirmation with message_id: {message_id}")
