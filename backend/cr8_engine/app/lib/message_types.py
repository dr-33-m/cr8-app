"""
Standardized Socket.IO Message Types for CR8 Engine
Phase 1: Type Definitions & Core Infrastructure

Using Pydantic for validation and serialization
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class MessageType(str, Enum):
    """Message types following state-based naming convention"""
    
    # Connection lifecycle
    SESSION_CREATED = "session_created"
    SESSION_READY = "session_ready"
    BLENDER_CONNECTED = "blender_connected"
    BLENDER_DISCONNECTED = "blender_disconnected"
    
    # Direct commands (UI controls)
    COMMAND_SENT = "command_sent"
    COMMAND_RECEIVED = "command_received"
    COMMAND_COMPLETED = "command_completed"
    COMMAND_FAILED = "command_failed"
    
    # Agent interactions (natural language)
    AGENT_QUERY_SENT = "agent_query_sent"
    AGENT_PROCESSING = "agent_processing"
    AGENT_RESPONSE_READY = "agent_response_ready"
    AGENT_ERROR = "agent_error"
    
    # System updates
    REGISTRY_UPDATED = "registry_updated"
    SCENE_CONTEXT_UPDATED = "scene_context_updated"
    INBOX_CLEARED = "inbox_cleared"
    
    # Errors
    CONNECTION_ERROR = "connection_error"
    VALIDATION_ERROR = "validation_error"
    EXECUTION_ERROR = "execution_error"


class MessageMetadata(BaseModel):
    """Message metadata for tracking and debugging"""
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())
    source: Literal["browser", "backend", "blender"]
    route: Literal["direct", "agent"]
    
    class Config:
        use_enum_values = True


class CommandPayload(BaseModel):
    """Payload for direct command messages (UI controls)"""
    addon_id: str
    command: str
    params: Dict[str, Any] = Field(default_factory=dict)


class AgentQueryPayload(BaseModel):
    """Payload for agent query messages (natural language)"""
    message: str
    context: Optional[Dict[str, Any]] = None


class ErrorDetails(BaseModel):
    """Error details with user-friendly messages"""
    code: str
    user_message: str = Field(..., description="Simple English from B.L.A.Z.E")
    technical_message: str = Field(..., description="For debugging/logs")
    recovery_suggestions: List[str] = Field(default_factory=list)


class ResponsePayload(BaseModel):
    """Payload for response messages"""
    status: Literal["success", "error"]
    data: Optional[Any] = None
    error: Optional[ErrorDetails] = None


class SystemPayload(BaseModel):
    """Payload for system update messages"""
    status: Optional[str] = None
    message: Optional[str] = None
    data: Optional[Any] = None


# Union type for all payload types
MessagePayload = Union[CommandPayload, AgentQueryPayload, ResponsePayload, SystemPayload]


class SocketMessage(BaseModel):
    """
    Universal Socket.IO message structure
    All messages must follow this format for consistency
    """
    message_id: str = Field(..., description="UUID for tracking (REQUIRED)")
    type: MessageType = Field(..., description="Message category (state-based)")
    payload: MessagePayload = Field(..., description="Message-specific data")
    metadata: Optional[MessageMetadata] = Field(None, description="Optional tracking information")
    
    class Config:
        use_enum_values = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for JSON serialization"""
        return self.model_dump(mode='json', exclude_none=True)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SocketMessage':
        """Create SocketMessage from dictionary with validation"""
        return cls.model_validate(data)


# Type guards
def is_command_payload(payload: Any) -> bool:
    """Check if payload is a CommandPayload"""
    return isinstance(payload, CommandPayload)


def is_agent_query_payload(payload: Any) -> bool:
    """Check if payload is an AgentQueryPayload"""
    return isinstance(payload, AgentQueryPayload)


def is_response_payload(payload: Any) -> bool:
    """Check if payload is a ResponsePayload"""
    return isinstance(payload, ResponsePayload)


def is_system_payload(payload: Any) -> bool:
    """Check if payload is a SystemPayload"""
    return isinstance(payload, SystemPayload)
