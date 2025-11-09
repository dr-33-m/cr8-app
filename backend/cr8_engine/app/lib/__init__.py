"""
Core library modules for CR8 Engine
"""

from .message_types import (
    MessageType,
    MessageMetadata,
    CommandPayload,
    AgentQueryPayload,
    ResponsePayload,
    SystemPayload,
    ErrorDetails,
    SocketMessage,
    is_command_payload,
    is_agent_query_payload,
    is_response_payload,
    is_system_payload,
)

from .message_utils import (
    generate_message_id,
    create_command_message,
    create_agent_query_message,
    create_success_response,
    create_error_response,
    create_system_message,
    translate_error,
    validate_message,
    is_valid_message_id,
    ERROR_TRANSLATIONS,
    RECOVERY_SUGGESTIONS,
)

__all__ = [
    # Types
    "MessageType",
    "MessageMetadata",
    "CommandPayload",
    "AgentQueryPayload",
    "ResponsePayload",
    "SystemPayload",
    "ErrorDetails",
    "SocketMessage",
    # Type guards
    "is_command_payload",
    "is_agent_query_payload",
    "is_response_payload",
    "is_system_payload",
    # Utilities
    "generate_message_id",
    "create_command_message",
    "create_agent_query_message",
    "create_success_response",
    "create_error_response",
    "create_system_message",
    "translate_error",
    "validate_message",
    "is_valid_message_id",
    "ERROR_TRANSLATIONS",
    "RECOVERY_SUGGESTIONS",
]
