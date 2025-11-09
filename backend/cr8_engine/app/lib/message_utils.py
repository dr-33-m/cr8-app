"""
Message Utilities for Socket.IO Communication
Phase 1: Type Definitions & Core Infrastructure

Provides helper functions for message creation, validation, and error handling
"""

import uuid
import logging
from typing import Dict, Any, Optional, Literal
from datetime import datetime

from .message_types import (
    SocketMessage,
    MessageType,
    MessageMetadata,
    CommandPayload,
    AgentQueryPayload,
    ResponsePayload,
    SystemPayload,
    ErrorDetails,
)

logger = logging.getLogger(__name__)


# ============================================================================
# UUID Generation
# ============================================================================

def generate_message_id() -> str:
    """
    Generate a unique message ID using UUID4
    
    Returns:
        str: Unique message identifier
    """
    return str(uuid.uuid4())


# ============================================================================
# Message Builders
# ============================================================================

def create_command_message(
    addon_id: str,
    command: str,
    params: Dict[str, Any],
    source: Literal["browser", "backend", "blender"] = "backend",
    message_id: Optional[str] = None
) -> SocketMessage:
    """
    Create a standardized command message
    
    Args:
        addon_id: Target addon identifier
        command: Command name to execute
        params: Command parameters
        source: Message source
        message_id: Optional message ID (generated if not provided)
    
    Returns:
        SocketMessage: Standardized command message
    """
    return SocketMessage(
        message_id=message_id or generate_message_id(),
        type=MessageType.COMMAND_SENT,
        payload=CommandPayload(
            addon_id=addon_id,
            command=command,
            params=params
        ),
        metadata=MessageMetadata(
            timestamp=datetime.now().timestamp(),
            source=source,
            route="direct"
        )
    )


def create_agent_query_message(
    message: str,
    context: Optional[Dict[str, Any]] = None,
    source: Literal["browser", "backend", "blender"] = "browser",
    message_id: Optional[str] = None
) -> SocketMessage:
    """
    Create a standardized agent query message
    
    Args:
        message: Natural language query
        context: Optional context (inbox items, scene objects, etc.)
        source: Message source
        message_id: Optional message ID (generated if not provided)
    
    Returns:
        SocketMessage: Standardized agent query message
    """
    return SocketMessage(
        message_id=message_id or generate_message_id(),
        type=MessageType.AGENT_QUERY_SENT,
        payload=AgentQueryPayload(
            message=message,
            context=context
        ),
        metadata=MessageMetadata(
            timestamp=datetime.now().timestamp(),
            source=source,
            route="agent"
        )
    )


def create_success_response(
    data: Any,
    message_id: str,
    source: Literal["browser", "backend", "blender"] = "backend",
    route: Literal["direct", "agent"] = "direct"
) -> SocketMessage:
    """
    Create a standardized success response message
    
    Args:
        data: Response data
        message_id: Original message ID for correlation
        source: Message source
        route: Message route (direct or agent)
    
    Returns:
        SocketMessage: Standardized success response
    """
    message_type = (
        MessageType.AGENT_RESPONSE_READY if route == "agent" 
        else MessageType.COMMAND_COMPLETED
    )
    
    return SocketMessage(
        message_id=message_id,
        type=message_type,
        payload=ResponsePayload(
            status="success",
            data=data
        ),
        metadata=MessageMetadata(
            timestamp=datetime.now().timestamp(),
            source=source,
            route=route
        )
    )


def create_error_response(
    error_code: str,
    user_message: str,
    technical_message: str,
    message_id: str,
    recovery_suggestions: Optional[list] = None,
    source: Literal["browser", "backend", "blender"] = "backend",
    route: Literal["direct", "agent"] = "direct"
) -> SocketMessage:
    """
    Create a standardized error response message
    
    Args:
        error_code: Error code identifier
        user_message: User-friendly error message
        technical_message: Technical error details
        message_id: Original message ID for correlation
        recovery_suggestions: Optional recovery suggestions
        source: Message source
        route: Message route (direct or agent)
    
    Returns:
        SocketMessage: Standardized error response
    """
    message_type = (
        MessageType.AGENT_ERROR if route == "agent" 
        else MessageType.COMMAND_FAILED
    )
    
    return SocketMessage(
        message_id=message_id,
        type=message_type,
        payload=ResponsePayload(
            status="error",
            error=ErrorDetails(
                code=error_code,
                user_message=user_message,
                technical_message=technical_message,
                recovery_suggestions=recovery_suggestions or []
            )
        ),
        metadata=MessageMetadata(
            timestamp=datetime.now().timestamp(),
            source=source,
            route=route
        )
    )


def create_system_message(
    message_type: MessageType,
    status: Optional[str] = None,
    message: Optional[str] = None,
    data: Optional[Any] = None,
    source: Literal["browser", "backend", "blender"] = "backend",
    message_id: Optional[str] = None
) -> SocketMessage:
    """
    Create a standardized system message
    
    Args:
        message_type: Type of system message
        status: Optional status
        message: Optional message text
        data: Optional data payload
        source: Message source
        message_id: Optional message ID (generated if not provided)
    
    Returns:
        SocketMessage: Standardized system message
    """
    return SocketMessage(
        message_id=message_id or generate_message_id(),
        type=message_type,
        payload=SystemPayload(
            status=status,
            message=message,
            data=data
        ),
        metadata=MessageMetadata(
            timestamp=datetime.now().timestamp(),
            source=source,
            route="direct"
        )
    )


# ============================================================================
# Error Translation
# ============================================================================

ERROR_TRANSLATIONS = {
    'COMMAND_NOT_FOUND': 'I couldn\'t find that command. Make sure Blender is connected and the addon is installed.',
    'INVALID_PARAMETERS': 'The parameters provided don\'t match what\'s expected for this command.',
    'EXECUTION_FAILED': 'Something went wrong while executing the command in Blender.',
    'BLENDER_DISCONNECTED': 'Blender is not connected. Please reconnect to continue.',
    'ADDON_ERROR': 'The addon encountered an error processing your request.',
    'VALIDATION_ERROR': 'The data provided couldn\'t be validated.',
    'TIMEOUT': 'The command took too long to execute. Blender might be busy.',
    'NO_HANDLERS': 'No command handlers found for this addon.',
    'ROUTING_FAILED': 'Failed to route the command to the appropriate handler.',
}

RECOVERY_SUGGESTIONS = {
    'BLENDER_DISCONNECTED': [
        'Check if Blender is still running',
        'Try reconnecting from the connection panel'
    ],
    'COMMAND_NOT_FOUND': [
        'Verify the addon is installed and enabled',
        'Try refreshing the addon registry'
    ],
    'ADDON_ERROR': [
        'Check the Blender console for detailed error messages',
        'Try restarting Blender if the issue persists'
    ],
    'TIMEOUT': [
        'Wait for Blender to finish current operations',
        'Try the command again in a moment'
    ],
}


def translate_error(
    error_code: str,
    technical_message: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Convert technical errors to user-friendly messages with recovery suggestions
    
    Args:
        error_code: Error code identifier
        technical_message: Technical error details
        context: Optional context for error translation
    
    Returns:
        Dict containing user_message and recovery_suggestions
    """
    base_message = ERROR_TRANSLATIONS.get(
        error_code,
        'Something unexpected happened.'
    )
    
    recovery_suggestions = RECOVERY_SUGGESTIONS.get(error_code, [])
    
    # Combine base message with technical details
    user_message = f"{base_message} {technical_message}"
    
    return {
        'user_message': user_message,
        'recovery_suggestions': recovery_suggestions
    }


# ============================================================================
# Message Validation
# ============================================================================

def validate_message(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate message structure
    
    Args:
        data: Message data to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Try to parse as SocketMessage
        SocketMessage.from_dict(data)
        return True, None
    except Exception as e:
        logger.error(f"Message validation failed: {str(e)}")
        return False, str(e)


def is_valid_message_id(message_id: str) -> bool:
    """
    Check if a message ID is valid UUID format
    
    Args:
        message_id: Message ID to validate
    
    Returns:
        bool: True if valid UUID format
    """
    try:
        uuid.UUID(message_id)
        return True
    except (ValueError, AttributeError):
        return False
