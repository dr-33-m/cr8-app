# System Patterns: Cr8-xyz Architecture

## Architecture Overview

The Cr8-xyz system follows a distributed, event-driven architecture with clear separation of concerns between frontend, Cr8 Engine (FastAPI), and Blender Creative Engine components. The system enables AI-assisted 3D content creation through natural language interfaces and real-time viewport streaming.

## Core Patterns

### WebSocket Message Routing

- **Pattern**: Dual endpoint architecture with pattern-based message routing
- **Implementation**: Messages are routed based on client type (browser/blender) and command structure
- **Tracking**: Session-based message correlation with unique message IDs
- **Location**: FastAPI WebSocket handlers with B.L.A.Z.E agent integration

### Session Management

- **Pattern**: Exponential backoff retry mechanism with browser refresh detection
- **Implementation**: Configurable retry limits, delay strategies, and session state tracking
- **Components**: Session managers in Cr8 Engine with Blender instance lifecycle management
- **Error Handling**: Graceful degradation, reconnection strategies, and timeout monitoring

### Session-Based Message Tracking

- **Pattern**: Request-response correlation using session-stored message tracking
- **Implementation**: Session.pending_refresh_commands dictionary for tracking commands that need scene refresh
- **Problem Solved**: Prevents response bypass where Blender → SessionManager → Browser skips WebSocketHandler
- **Triggers**: Automatic scene context refresh when tracked commands succeed
- **Location**: SessionManager.forward_message() checks for successful responses to tracked message_ids

### AI Agent Integration

- **Pattern**: Dynamic toolset generation from addon manifests
- **Implementation**: B.L.A.Z.E agent with Pydantic AI that builds capabilities from discovered addons
- **Tracking**: Real-time registry updates and capability discovery
- **Validation**: Parameter validation against manifest specifications

### Addon Registry and Discovery

- **Pattern**: Manifest-based addon discovery with standardized ai_integration format
- **Implementation**: AI Router addon scans for addon_ai.json files and validates capabilities
- **Limits**: Type-safe parameter validation and standardized tool specifications
- **Monitoring**: Real-time registry updates via WebSocket events

## Component Relationships

### Frontend ↔ Cr8 Engine

- **Communication**: WebSocket-based real-time messaging with WebRTC viewport streaming
- **Pattern**: Sends natural language commands and receives AI agent responses
- **Data Flow**: Bidirectional with request-response patterns and real-time viewport updates

### Cr8 Engine ↔ Blender Creative Engine

- **Communication**: Direct WebSocket control through AI Router addon
- **Pattern**: Command execution with dynamic addon routing and parameter validation
- **Data Flow**: Synchronous operations with async feedback and registry event streaming

### Frontend ↔ Blender Creative Engine

- **Communication**: Indirect control through Cr8 Engine proxy with WebRTC streaming
- **Pattern**: Natural language interface to Blender operations with real-time viewport feedback
- **Data Flow**: Coordinated state synchronization with AI-assisted workflow automation

## Error Handling Patterns

### Connection Errors

- **Strategy**: Retry with exponential backoff and browser refresh detection
- **Limits**: Configurable maximum attempts with intelligent delay strategies
- **Recovery**: Automatic reconnection with existing Blender instance detection

### Message Processing Errors

- **Strategy**: Notification-based error reporting with detailed context
- **Logging**: Comprehensive error context, stack traces, and parameter validation feedback
- **Recovery**: Automatic retry for transient errors, manual intervention for critical failures

### AI Agent Errors

- **Strategy**: Model retry mechanisms with parameter validation feedback
- **Validation**: Real-time parameter checking against addon manifest specifications
- **Rollback**: Context-aware error handling with user-friendly feedback

## Integration Patterns

### Dynamic AI Capabilities

- **Pattern**: Runtime capability discovery and toolset generation
- **Triggers**: Addon installation/removal and registry updates
- **Synchronization**: Real-time system prompt updates and tool registration
- **Security**: Manifest validation and parameter type checking

### Context Management

- **Pattern**: Session-based context with real-time scene state updates
- **Scope**: Scene objects, addon capabilities, and user interaction history
- **Storage**: In-memory context managers with user isolation

### Refresh Context Tracking Pattern

- **Pattern**: Session-based tracking of commands that require scene context updates
- **Problem**: Direct UI commands with refresh_context=true weren't triggering scene updates
- **Root Cause**: Response flow bypassed WebSocketHandler: Blender → SessionManager → Browser
- **Solution**: Track refresh_context commands in session, trigger refresh in SessionManager.forward_message()
- **Implementation**:
  - WebSocketHandler.\_forward_message() stores message_id in session.pending_refresh_commands
  - SessionManager.forward_message() checks successful responses against tracked message_ids
  - SessionManager.\_trigger_scene_context_refresh() automatically calls list_scene_objects
  - Scene context updates propagate to browser via established WebSocket patterns
- **Benefits**: Automatic scene synchronization, no manual refresh buttons, consistent UI state
