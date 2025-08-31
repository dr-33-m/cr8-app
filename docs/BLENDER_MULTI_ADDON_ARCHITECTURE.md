# Blender Multi Addon Architecture Implementation

## Overview

This document describes the implementation of the Blender Multi Addon Architecture Specification v0.1, which transforms the Cr8-xyz system from a monolithic Blender addon to a marketplace-ready router architecture. This enables dynamic capability discovery where users can install AI-capable addons that immediately extend B.L.A.Z.E (the AI agent) capabilities.

## Architecture Transformation

### Before: Monolithic System

```
Frontend ↔ FastAPI (cr8_engine) ↔ WebSocket ↔ blender_cr8tive_engine (Monolithic Addon)
```

### After: Router-Based System

```
Frontend ↔ FastAPI (cr8_engine) ↔ WebSocket ↔ AI Router Addon ↔ Capability Addons
                ↓
            B.L.A.Z.E Agent (Dynamic Capabilities)
```

## Key Components Implemented

### 1. AI Router Addon (`backend/blender_cr8tive_engine/`)

The main addon was transformed from a monolithic system to a pure router that:

- Discovers AI-capable addons through manifest scanning
- Routes commands to appropriate capability addons
- Handles WebSocket communication with the FastAPI backend
- Manages dynamic capability registration

**Key Files:**

- `__init__.py` - Router addon entry point with command handlers
- `addon_ai.json` - Router's own AI capability manifest
- `registry/addon_registry.py` - Core registry for addon discovery and validation
- `registry/command_router.py` - Command routing and parameter validation
- `ws/websocket_handler.py` - Updated WebSocket handler for registry events

### 2. Addon Manifest Standard

**Format: `addon_ai.json`**

```json
{
  "addon_info": {
    "id": "addon_identifier",
    "name": "Human Readable Name",
    "version": "0.1.0",
    "author": "Developer Name",
    "category": "modeling|animation|rendering|simulation|io|utility|procedural|texturing|sculpting",
    "description": "Brief description"
  },
  "ai_integration": {
    "agent_description": "Natural language description for AI agent",
    "tools": [
      {
        "name": "tool_name",
        "description": "What this tool does",
        "usage": "When/why to use this tool",
        "parameters": [
          {
            "name": "param_name",
            "type": "string|integer|float|boolean|object_name|material_name|collection_name|enum|vector3|color|file_path",
            "description": "Parameter description",
            "required": true|false,
            "default": "default_value",
            "min": 0,
            "max": 100,
            "options": ["option1", "option2"]
          }
        ],
        "examples": ["Natural language usage examples"]
      }
    ],
    "context_hints": ["Guidelines for AI usage"],
    "requirements": {
      "blender_version_min": "4.0",
      "depends_on": ["required_addon_ids"],
      "conflicts_with": ["conflicting_addon_ids"]
    }
  }
}
```

### 3. Command Handler Standard

Each AI-capable addon MUST export command handlers:

```python
# In addon's __init__.py
def example_tool_handler(**kwargs) -> dict:
    """Standard handler function signature"""
    try:
        # Implementation here
        return {
            "status": "success",
            "message": "Operation completed successfully",
            "data": {}  # Optional additional data
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "error_code": "OPERATION_FAILED"
        }

AI_COMMAND_HANDLERS = {
    "example_tool": example_tool_handler,
    # ... more handlers
}
```

### 4. Registry System (`backend/blender_cr8tive_engine/registry/`)

#### AIAddonRegistry (`addon_registry.py`)

- **Purpose**: Discovers and validates AI-capable addons
- **Key Methods**:
  - `scan_addons()` - Scans Blender addon directories for `addon_ai.json` files
  - `validate_manifest()` - Validates manifest format and requirements
  - `register_addon()` - Registers addon in the system
  - `get_available_tools()` - Returns all available tools for agent context

#### AICommandRouter (`command_router.py`)

- **Purpose**: Routes commands to appropriate addons with parameter validation
- **Key Methods**:
  - `route_command()` - Routes command to appropriate addon handler
  - `execute_command()` - Executes command on specific addon
- **Features**:
  - Comprehensive parameter validation
  - Type checking (string, integer, float, boolean, vector3, color, enum, etc.)
  - Standardized error handling

**Key Features:**

- **Dynamic Tool Registration**: Auto-generates MCP tools from addon manifests
- **Runtime Capability Discovery**: Updates available tools when addons are installed/removed
- **Dynamic System Prompts**: AI agent context updates automatically with new capabilities

### 6. Updated B.L.A.Z.E Agent (`backend/cr8_engine/app/blaze/agent.py`)

Enhanced to handle dynamic capabilities:

- **Registry Update Handling**: Processes addon registry changes
- **Dynamic Capability Integration**: Automatically gains new abilities when addons are installed
- **Graceful Degradation**: Handles scenarios when no addons are available

## WebSocket Communication Protocol

### Command Format (FastAPI → Blender)

```json
{
  "type": "addon_command",
  "addon_id": "target_addon",
  "command": "command_name",
  "params": {
    "parameter_name": "parameter_value"
  },
  "request_id": "uuid-string",
  "username": "user123"
}
```

### Response Format (Blender → FastAPI)

```json
{
  "type": "command_response",
  "request_id": "uuid-string",
  "addon_id": "target_addon",
  "command": "command_name",
  "result": {
    "status": "success|error|warning",
    "message": "Human-readable status message",
    "data": {}
  }
}
```

### Registry Events (Blender → FastAPI)

```json
{
  "type": "addon_registered",
  "addon_id": "new_addon",
  "manifest": {...}
}

{
  "type": "addon_unregistered",
  "addon_id": "removed_addon"
}

{
  "type": "registry_updated",
  "available_addons": [...]
}
```

## Implementation Timeline

### Phase 1: Core Infrastructure ✅

- [x] Main AI addon registry and router
- [x] Manifest loading and validation
- [x] Basic command routing
- [x] WebSocket protocol implementation

### Phase 2: Dynamic Integration ✅

- [x] FastAPI dynamic tool registration
- [x] Agent context generation
- [x] B.L.A.Z.E agent dynamic capabilities
- [x] Registry event system

### Phase 3: Dependency Issue Resolution ✅

- [x] **Problem**: "no module named yaml" error when installing in Blender
- [x] **Root Cause**: PyYAML not included in Blender's Python environment
- [x] **Solution**: Converted entire system from YAML to JSON format
- [x] **Changes Made**:
  - Converted `addon_ai.yaml` to `addon_ai.json` format
  - Updated `addon_registry.py` to use `json.load()` instead of `yaml.safe_load()`
  - Removed all `import yaml` statements
  - Used built-in `json` module (available in Blender)

### Phase 4: Type Hints Compatibility Fix ✅

- [x] **Problem**: Multiple typing errors during Blender addon installation:
  - `NameError: name 'List' is not defined`
  - `NameError: name 'Dict' is not defined`
  - `NameError: name 'Any' is not defined`
- [x] **Root Cause**: Blender's Python environment has limited `typing` module support during runtime
- [x] **Solution**: Comprehensive typing compatibility strategy using only built-in types
- [x] **Final Resolution**: Eliminated ALL advanced typing constructs in favor of built-in types:
  - Removed all `typing.TYPE_CHECKING` imports and guards
  - Replaced `List[Type]` with simple `list` return type annotations
  - Replaced `Dict[str, Type]` with simple `dict` parameter and return types
  - Replaced `Optional[Type]` with simple untyped return values
  - Removed all `Any` type annotations entirely
  - Used only basic built-in types: `str`, `bool`, `int`, `dict`, `list`
- [x] **Files Updated**:
  - `backend/blender_cr8tive_engine/registry/addon_registry.py` - Complete rewrite with built-in types only
  - `backend/blender_cr8tive_engine/registry/command_router.py` - Complete rewrite with built-in types only
- [x] **Result**: 100% Blender Python environment compatibility with zero typing-related errors

### Phase 5: Session-Based Singleton Fix ✅ ⭐ **CRITICAL FIX**

- [x] **Problem**: Multiple B.L.A.Z.E agent instances causing capability mismatch:
  - Registry updates going to Agent Instance A (storing manifests)
  - Message processing happening in Agent Instance B (empty manifests)
  - Result: B.L.A.Z.E couldn't access dynamically registered tools
- [x] **Root Cause**: New agent instance created for each message processing
- [x] **Debug Evidence**:
  ```
  Agent Instance 140353637332944 (registry updates)
  Agent Instance 140353637726416 (message processing)
  ```
- [x] **Solution**: Session-based singleton pattern for B.L.A.Z.E agents
- [x] **Implementation**:

  ```python
  # session_manager.py
  class Session:
      def __init__(self, username: str, browser_socket: Optional[WebSocket] = None):
          # ... existing fields ...
          self.blaze_agent = None  # Single agent per session

  # websocket_handler.py
  if session and session.blaze_agent is None:
      session.blaze_agent = BlazeAgent(session_manager, handlers)
  self.blaze_agent = session.blaze_agent
  ```

- [x] **Files Updated**:
  - `backend/cr8_engine/app/realtime_engine/websockets/session_manager.py` - Added `blaze_agent = None` to Session class
  - `backend/cr8_engine/app/realtime_engine/websockets/websocket_handler.py` - Single agent creation and reuse
- [x] **Result**: Same agent instance handles both registry updates and message processing

### Phase 6: Pydantic AI Integration Fix ✅

- [x] **Problem**: `ImportError: cannot import name 'Toolset' from 'pydantic_ai'`
- [x] **Root Cause**: `Toolset` class doesn't exist in Pydantic AI - only `FunctionToolset`
- [x] **Solution**: Used proper Pydantic AI patterns with `FunctionToolset`
- [x] **Implementation**:
  ```python
  # agent.py
  @agent.toolset
  def _build_dynamic_toolset(self, ctx: RunContext) -> Optional[FunctionToolset]:
      if not self.addon_manifests:
          return None
      tools = []
      for manifest in self.addon_manifests:
          for tool in manifest.get('tools', []):
              # Create function tools dynamically
      return FunctionToolset(*tools) if tools else None
  ```
- [x] **Files Updated**:
  - `backend/cr8_engine/app/blaze/agent.py` - Proper `FunctionToolset` usage
- [x] **Result**: B.L.A.Z.E agent correctly builds dynamic toolsets from addon manifests

### Phase 7: FastMCP API Compatibility Fix ✅

- [x] **Problem**: `AttributeError: 'FastMCP' object has no attribute '_tools'`
- [x] **Root Cause**: Direct access to private `_tools` attribute not supported in FastMCP API
- [x] **Solution**: Used proper FastMCP API methods and tool name tracking
- [x] **Implementation**:

  ```python
  # mcp_server.py
  class DynamicMCPServer:
      def __init__(self):
          self.registered_tool_names = set()  # Track registered tools

      def refresh_capabilities(self, addon_manifests):
          # Remove existing tools using proper API
          for tool_name in list(self.registered_tool_names):
              try:
                  self.server.remove_tool(tool_name)
              except Exception as e:
                  logger.warning(f"Failed to remove tool {tool_name}: {e}")
          self.registered_tool_names.clear()
  ```

- [x] **Files Updated**:
  - `backend/cr8_engine/app/blaze/mcp_server.py` - Proper `remove_tool()` usage and tool tracking
- [x] **Result**: Dynamic tool registration/removal works correctly with FastMCP

### Phase 8: Working Test Implementation ✅ 🎯 **PROVEN SUCCESS**

- [x] **Created Test Addon**: `backend/test_addons/random_mesh_generator/`
- [x] **Addon Manifest**: Complete `addon_ai.json` with 4 mesh generation tools:
  - `add_random_cube` - Creates cubes with random properties
  - `add_random_sphere` - Creates spheres with random properties
  - `add_random_cylinder` - Creates cylinders with random properties
  - `add_surprise_mesh` - Creates random mesh type
- [x] **Command Handlers**: Full implementation in `__init__.py` with `AI_COMMAND_HANDLERS`
- [x] **End-to-End Test Results**:
  ```
  Registry Discovery: ✅ "1 addons, 4 tools"
  Dynamic Registration: ✅ "Registered 4 dynamic tools"
  B.L.A.Z.E Integration: ✅ "Built dynamic toolset with 4 tools"
  User Request: "add a random cube"
  Tool Execution: ✅ "Executing random_mesh_generator.add_random_cube"
  Blender Result: ✅ "Created random cube 'RandomCube' at [0.008..., 0.082..., 0.013...]"
  ```
- [x] **Architecture Validation**: Complete marketplace workflow proven working:
  1. Install addon → Router discovers capabilities ✅
  2. Dynamic registration → Tools available to B.L.A.Z.E ✅
  3. Natural language → B.L.A.Z.E uses correct tool ✅
  4. Command execution → Blender creates objects ✅

## Marketplace Foundation

The implemented architecture enables:

### 1. **Instant Integration**

- Users install an addon → Router discovers it → B.L.A.Z.E gains new capabilities
- No system restart or configuration required

### 2. **Standardized Development**

- Addon developers follow the manifest specification
- Consistent parameter validation and error handling
- Standard response formats

### 3. **Dynamic AI Capabilities**

- AI system prompt updates automatically with new addon capabilities
- MCP tools generated dynamically from addon manifests
- Real-time capability discovery

### 4. **Seamless User Experience**

- Users see new AI capabilities immediately after addon installation
- Natural language interaction with new addon features
- Integrated error handling and validation

### 5. **Scalable Architecture**

- Supports unlimited capability addons without core system changes
- Isolated addon execution through router pattern
- Conflict detection and dependency management

## Testing and Validation

### Installation Testing

```bash
# Test router addon installation in Blender
# Should install without dependency errors
# All JSON parsing should work with built-in modules
```

### Registry Testing

```python
# Test addon discovery
registry.scan_addons()

# Test manifest validation
registry.validate_manifest(manifest_data)

# Test command routing
router.route_command("addon_id", "command_name", params)
```

### Dynamic Capability Testing

```python
# Test MCP server dynamic registration
mcp_server.refresh_capabilities(manifests)

# Test agent context generation
agent_context = mcp_server.build_agent_context(manifests)
```

## Next Steps

### Phase 4: Example Capability Addons (Future)

- Create demonstration addons following the specification
- Mesh optimization addon example
- Animation tools addon example
- Rendering utilities addon example

### Phase 5: Marketplace Integration (Future)

- Addon marketplace UI/UX
- Installation automation
- Version management
- User ratings and reviews

## Developer Guidelines

### Creating AI-Capable Addons

1. **Create Manifest**: Add `addon_ai.json` to addon root
2. **Implement Handlers**: Create functions with standard signatures
3. **Export Handlers**: Add to `AI_COMMAND_HANDLERS` dictionary
4. **Test Integration**: Verify router discovery and command execution
5. **Document Examples**: Provide natural language usage examples

### Best Practices

- **Parameter Validation**: Always validate input parameters
- **Error Handling**: Return standardized error responses
- **Performance**: Keep command handlers efficient
- **Documentation**: Provide clear descriptions and examples
- **Testing**: Unit test all command handlers

## File Structure

```
backend/blender_cr8tive_engine/
├── __init__.py                 # Router addon entry point
├── addon_ai.json              # Router's AI manifest
├── registry/
│   ├── __init__.py
│   ├── addon_registry.py      # Core registry system
│   └── command_router.py      # Command routing & validation
├── ws/
│   └── websocket_handler.py   # WebSocket communication
└── [existing addon structure]

backend/cr8_engine/app/blaze/
├── mcp_server.py              # Dynamic MCP server
├── agent.py                   # Updated B.L.A.Z.E agent
└── [existing blaze structure]
```

This architecture successfully transforms the Cr8-xyz system into a marketplace-ready platform where AI capabilities can be dynamically extended through addon installations.
