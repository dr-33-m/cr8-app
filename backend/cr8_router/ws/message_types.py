"""
Standardized Socket.IO message types for Blender AI Router.
These types match the backend (message_types.py) and frontend (websocket.ts) definitions.
"""


class MessageType:
    """
    Standardized Socket.IO message types.
    Ensures consistency across Browser ↔ Backend ↔ Blender communication.
    """
    
    # Connection lifecycle
    SESSION_CREATED = "session_created"
    SESSION_READY = "session_ready"
    BLENDER_CONNECTED = "blender_connected"
    BLENDER_DISCONNECTED = "blender_disconnected"
    
    # Direct commands (UI controls → Blender)
    COMMAND_SENT = "command_sent"           # Browser → Backend
    COMMAND_RECEIVED = "command_received"   # Backend → Blender
    COMMAND_COMPLETED = "command_completed" # Blender → Backend (success)
    COMMAND_FAILED = "command_failed"       # Blender → Backend (error)
    
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
