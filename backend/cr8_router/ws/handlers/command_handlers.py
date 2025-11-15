"""
Command processing and routing handlers for WebSocket messages.
Handles message deduplication, command routing, and addon command execution.
"""

import json
import logging
from ..utils.response_manager import ResponseManager

logger = logging.getLogger(__name__)


def process_message(data, handler):
    """
    Process incoming message with deduplication.
    
    Args:
        data: Message data from Socket.IO
        handler: WebSocketHandler instance
    """
    try:
        logger.info(f"Processing incoming message: {data}")
        
        # Get both type and command fields
        message_type = data.get('type')
        command = data.get('command')
        message_id = data.get('message_id')

        logger.info(
            f"Parsed message - type: {message_type}, command: {command}, message_id: {message_id}")

        # Create unique command key using type or command
        command_identifier = message_type or command
        command_key = (command_identifier, message_id) if message_id else None

        # Validation safety net: warn about missing message IDs for important commands
        if not message_id and command_identifier not in ['ping', 'connection_confirmation']:
            logger.warning(
                f"Command {command_identifier} received without message_id - this may cause deduplication issues")

        # Check if already processed
        if command_key and command_key in handler.processed_commands:
            logger.warning(
                f"Skipping already processed command: {command_identifier} with message_id: {message_id}")
            return

        # Check if currently processing (CRITICAL: prevents duplicate execution)
        if command_key and command_key in handler.processing_commands:
            logger.warning(
                f"Command {command_identifier} with message_id {message_id} still processing, ignoring duplicate")
            return

        # Mark as processing
        if command_key:
            handler.processing_commands.add(command_key)

        if not command_identifier:
            logger.warning(
                f"Received message without a valid type or command: {data}")
            return

        logger.info(f"Looking for handler for type: {message_type}, command: {command}")

        # Route based on message type first, then command
        if message_type == 'addon_command':
            # Handle addon commands through router (AI-routed commands)
            handle_addon_command(data, handler)
            
        elif command == 'ping':
            # Handle utility commands directly
            from .utility_handlers import handle_ping
            handle_ping(data, handler)

        elif command == 'connection_confirmation':
            from .utility_handlers import handle_connection_confirmation
            handle_connection_confirmation(data, handler)

        elif command:
            # Route all other commands through the AI router (direct commands)
            route_command_to_addon(command, data, handler)
        
        else:
            logger.warning(f"Unknown message type/command: type={message_type}, command={command}")

        # Mark as processed and remove from processing
        if command_key:
            handler.processing_commands.discard(command_key)
            handler.processed_commands.add(command_key)
            logger.info(
                f"Marked command {command_identifier} with message_id {message_id} as processed")

    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON message: {e}")
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        import traceback
        traceback.print_exc()
        # Ensure we remove from processing on error
        if 'command_key' in locals() and command_key and command_key in handler.processing_commands:
            handler.processing_commands.discard(command_key)


def handle_addon_command(data, handler):
    """
    Handle structured addon commands with route preservation.
    
    Args:
        data: Command data from Socket.IO
        handler: WebSocketHandler instance
    """
    try:
        addon_id = data.get('addon_id')
        command = data.get('command')
        params = data.get('params', {})
        message_id = data.get('message_id')
        
        # Extract route from incoming command (critical for proper response routing)
        # Check both metadata.route and direct route field for compatibility
        route = 'direct'  # Default
        if 'metadata' in data:
            route = data['metadata'].get('route', 'direct')
        elif 'route' in data:
            route = data.get('route', 'direct')

        logger.info(
            f"Handling addon command: {addon_id}.{command} with params: {params}, route: {route}")

        # Get router instance
        from ... import get_router
        router = get_router()

        # Execute command through router
        result = router.execute_command(addon_id, command, params)

        # Send response with preserved route
        response_manager = ResponseManager.get_instance()
        response_manager.send_response(
            f"{command}_result",
            result.get('status') == 'success',
            result,
            message_id,
            route=route  # Preserve route for proper forwarding
        )

    except Exception as e:
        logger.error(f"Error handling addon command: {str(e)}")
        response_manager = ResponseManager.get_instance()
        
        # Extract route for error response too
        route = 'direct'
        if 'metadata' in data:
            route = data['metadata'].get('route', 'direct')
        elif 'route' in data:
            route = data.get('route', 'direct')
            
        response_manager.send_response(
            f"{command}_result",
            False,
            {
                "status": "error",
                "message": f"Command handling failed: {str(e)}",
                "error_code": "COMMAND_HANDLING_ERROR"
            },
            data.get('message_id'),
            route=route
        )


def route_command_to_addon(command, data, handler):
    """
    Route commands through the AI router using structured format.
    
    Args:
        command: Command name
        data: Command data from Socket.IO
        handler: WebSocketHandler instance
    """
    try:
        # Extract parameters from structured format only
        params = data.get('params', {})
        addon_id = data.get('addon_id')
        message_id = data.get('message_id')

        logger.info(
            f"Routing command: {command} with params: {params}, addon_id: {addon_id}")

        # Get router instance
        from ... import get_router
        router = get_router()

        # Route command to appropriate addon (with addon_id if available)
        if addon_id:
            result = router.execute_command(addon_id, command, params)
        else:
            result = router.route_command(command, params)

        # Send response
        response_manager = ResponseManager.get_instance()
        response_manager.send_response(
            f"{command}_result",
            result.get('status') == 'success',
            result,
            message_id
        )

    except Exception as e:
        logger.error(f"Error routing command to addon: {str(e)}")
        response_manager = ResponseManager.get_instance()
        response_manager.send_response(
            f"{command}_result",
            False,
            {
                "status": "error",
                "message": f"Command routing failed: {str(e)}",
                "error_code": "ROUTING_ERROR"
            },
            data.get('message_id')
        )
