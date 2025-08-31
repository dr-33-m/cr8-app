# B.L.A.Z.E Architecture Documentation

## Overview

B.L.A.Z.E (Blender's Artistic Zen Engineer) is an AI agent that provides natural language control over 3D scenes in Blender through dynamic toolsets. This document outlines the complete architecture, learned through extensive debugging and optimization.

## Core Architecture

```
User Request → B.L.A.Z.E Agent → Dynamic Toolset → Direct WebSocket → Blender Addons
```

### Key Components

1. **B.L.A.Z.E Agent** (`backend/cr8_engine/app/blaze/agent.py`)
2. **Context Manager** (`backend/cr8_engine/app/blaze/context_manager.py`)
3. **Dynamic Addon System** (Registry + Manifests)
4. **WebSocket Communication** (Direct, no MCP layer)

## B.L.A.Z.E Agent Architecture

### Core Class: `BlazeAgent`

```python
class BlazeAgent:
    def __init__(self, session_manager, handlers, model_name):
        # Pydantic AI Agent with OpenRouter
        self.agent = Agent(self.model, system_prompt=self._get_dynamic_system_prompt())

        # Dynamic toolset registration
        @self.agent.toolset
        def dynamic_addon_toolset(ctx: RunContext) -> Optional[FunctionToolset]:
            return self._build_dynamic_toolset(ctx)
```

### Dynamic Capabilities

**B.L.A.Z.E's capabilities are 100% dynamic:**

- Tools appear/disappear based on installed Blender addons
- Each addon provides its own tools via manifest files
- System prompt updates in real-time based on available addons
- No hardcoded functionality - everything comes from addons

## Addon Manifest Structure (Standardized)

### Official Format: `ai_integration` Structure

```json
{
  "addon_info": {
    "id": "unique_addon_id",
    "name": "Human Readable Name",
    "version": "1.0.0",
    "author": "Author Name",
    "category": "category_name",
    "description": "Basic addon description"
  },
  "ai_integration": {
    "agent_description": "Description for B.L.A.Z.E about capabilities",
    "tools": [
      {
        "name": "tool_function_name",
        "description": "What this tool does",
        "usage": "When to use this tool",
        "category": "tool_category",
        "parameters": [
          {
            "name": "parameter_name",
            "type": "string|float|integer|boolean|enum",
            "description": "Parameter description",
            "required": true|false,
            "default": "default_value",
            "options": ["option1", "option2"] // for enum types
          }
        ],
        "examples": ["example usage 1", "example usage 2"]
      }
    ],
    "context_hints": [
      "When to suggest this addon",
      "Usage scenarios"
    ],
    "requirements": {
      "blender_version_min": "3.0.0",
      "dependencies": ["numpy"],
      "api_keys": {"service": "required|not_required"}
    },
    "metadata": {
      "priority": 85,
      "performance_impact": "low|medium|high",
      "experimental": false
    }
  }
}
```

### Parameter Types Supported

- `string` → `str`
- `integer` → `int`
- `float` → `float`
- `boolean` → `bool`
- `enum` → `str` with `options` array
- `vector3` → `List[float]`
- `object_name` → `str` (semantic type)

## Dynamic Toolset Generation

### The Core Innovation: Real Parameter Schemas

**Problem Solved:** B.L.A.Z.E was seeing generic `**kwargs` functions and creating its own semantic parameter names instead of using manifest definitions.

**Solution:** Dynamic function generation with explicit parameter signatures.

### Function Generation Process

```python
def _create_dynamic_tool_function(self, addon_id, tool_name, tool_description, tool_params):
    # Build signature: place_object_relative(object1_name, object2_name, side, distance)
    signature_str = ', '.join(param_signature_parts)

    # Generate complete function with explicit parameters
    function_code = f'''
async def {tool_name}({signature_str}):
    """
    {tool_description}
    """
    all_params = {param_dict_code}
    filtered_params = {{k: v for k, v in all_params.items() if v is not None}}
    return await self.execute_addon_command_direct('{addon_id}', '{tool_name}', filtered_params)
'''

    exec(function_code, namespace)
    return namespace[tool_name]
```

### Before vs After

**Before (Broken):**

```python
async def tool_function(**kwargs) -> str:
    # B.L.A.Z.E sees no parameters, creates semantic names
    # Result: {'object_to_move': 'Chair', 'reference_object': 'Table'}
```

**After (Fixed):**

```python
async def place_object_relative(object1_name: str, object2_name: str, side: str, distance: float) -> str:
    # B.L.A.Z.E sees exact parameter names from manifest
    # Result: {'object1_name': 'Chair', 'object2_name': 'Table', 'side': 'right', 'distance': 0.5}
```

## WebSocket Communication Flow

### Direct Communication (No MCP Layer)

```python
async def execute_addon_command_direct(self, addon_id: str, command: str, params: Dict[str, Any]) -> str:
    message = {
        "type": "addon_command",
        "addon_id": addon_id,
        "command": command,
        "params": params,
        "username": self.current_username,
        "message_id": str(uuid.uuid4())
    }

    session = self.session_manager.get_session(self.current_username)
    await session.blender_socket.send_json(message)
```

### Message Flow

1. **User Input** → Natural language request
2. **B.L.A.Z.E Processing** → Analyzes request, selects tools
3. **Tool Execution** → Calls functions with proper parameters
4. **WebSocket Message** → Direct to Blender addon
5. **Addon Processing** → Executes command in Blender
6. **Context Refresh** → Updates scene state for next operations

## Registry and Discovery System

### Addon Discovery Flow

```python
def handle_registry_update(self, registry_data: Dict[str, Any]) -> None:
    # Convert registry data to standardized ai_integration format
    for tool in available_tools:
        manifest = {
            'addon_info': {'id': addon_id, 'name': addon_name},
            'ai_integration': {
                'agent_description': description,
                'tools': addon_tools,
                'context_hints': []
            }
        }

    # Store manifests for dynamic toolset
    self.addon_manifests = manifests
```

### Registry Components

- **Addon Registry** (`backend/blender_cr8tive_engine/registry/addon_registry.py`)
- **Command Router** (`backend/blender_cr8tive_engine/registry/command_router.py`)
- **WebSocket Handler** (`backend/blender_cr8tive_engine/ws/websocket_handler.py`)

## System Prompt Generation

### Dynamic Context Building

```python
def _build_agent_context(self, manifests: List[Dict[str, Any]]) -> str:
    # For each addon manifest:
    for manifest in manifests:
        ai_integration = manifest['ai_integration']
        addon_info = manifest['addon_info']

        # Add tools with parameter information
        for tool in tools:
            required_params = [p['name'] for p in tool_params if p.get('required', True)]
            optional_params = [p['name'] for p in tool_params if not p.get('required', True)]
            param_info = f" (required: {', '.join(required_params)}; optional: {', '.join(optional_params)})"

            base_prompt += f"- {tool_name}: {tool_description}{param_info}\n"
```

### Context Information Provided

- **Tool Descriptions** with explicit parameter names
- **Parameter Requirements** (required vs optional)
- **Usage Guidelines** emphasizing exact parameter names
- **Context Hints** for when to use each addon

## Scene Context Management

### Universal Context Refresh System

After every command execution, B.L.A.Z.E automatically refreshes scene context:

```python
async def _refresh_scene_context_universal(self, username: str) -> None:
    # Find any addon that provides list_scene_objects
    # Execute list_scene_objects to get current scene state
    # Updates context manager with current object list
```

### Context Manager Integration

- **Scene Object Tracking** - Knows what objects are available
- **Spatial Relationships** - Understands object positions
- **Dynamic Updates** - Refreshes after every operation

## Key Architectural Decisions

### Why We Removed MCP

**Problem:** We had redundant architecture:

```
B.L.A.Z.E → Pydantic AI Toolset (**kwargs) → MCP Server (proper schemas) → WebSocket
                ↑
            Used by B.L.A.Z.E (broken)              ↑
                                              Unused (working)
```

**Solution:** Direct Pydantic AI approach:

```
B.L.A.Z.E → Pydantic AI Toolset (proper schemas) → WebSocket
```

### Why Standardized on `ai_integration`

- **Cleaner Code** - No version compatibility checks
- **Consistent Structure** - All addons use same format
- **Easier Maintenance** - Single code path to handle
- **Future-Proof** - System still in development, no legacy burden

## Parameter Schema System

### Critical Parameter Recognition Fix

**Root Cause:** B.L.A.Z.E was creating semantic parameter names because it only saw generic `**kwargs` functions.

**Solution:** Generate functions with explicit parameter signatures from manifests.

### Parameter Mapping

```python
type_mapping = {
    'string': str,
    'integer': int,
    'float': float,
    'boolean': bool,
    'enum': str,  # with options array
    'vector3': List[float],
    'object_name': str,
    'material_name': str,
    'collection_name': str,
    'file_path': str
}
```

### Enum Parameter Handling

```python
# Manifest definition:
{
  "name": "side",
  "type": "enum",
  "options": ["left", "right", "top", "bottom", "front", "back"],
  "required": true
}

# Generated function signature:
async def place_object_relative(..., side, ...):
```

## Error Patterns and Solutions

### Common Parameter Recognition Issues

1. **Generic `**kwargs`\*\* → B.L.A.Z.E creates semantic names
2. **Missing Required Parameters** → B.L.A.Z.E doesn't know what's required
3. **Wrong Parameter Names** → Function signature mismatch errors

### Debugging Approach

1. **Check System Prompt** - What does B.L.A.Z.E see in tool descriptions?
2. **Verify Function Signatures** - Are functions generated with proper parameters?
3. **Trace Parameter Flow** - From manifest → function → B.L.A.Z.E → WebSocket
4. **Check Manifest Structure** - Is data being read correctly?

## Performance and Scalability

### Dynamic Tool Registration

- **Efficient** - Tools only created when addons are available
- **Memory Conscious** - Old tools removed when addons unloaded
- **Real-time** - Capabilities update immediately when addon state changes

### Context Management

- **Lazy Loading** - Scene context only fetched when needed
- **Automatic Updates** - Context refreshed after operations
- **User Isolation** - Each user has separate context

## Future Architecture Considerations

### Multi-Registry Support

Current implementation ready for:

- **Polyhaven** (implemented)
- **BlenderKit** (ready to add)
- **Additional Registries** (extensible pattern)

### AI Enhancement Opportunities

- **Intelligent Parameter Inference** - B.L.A.Z.E could suggest parameter values
- **Scene Analysis** - AI-powered spatial relationship understanding
- **Command Chaining** - Complex multi-step operations
- **Error Recovery** - Automatic parameter correction

## Debugging Tools and Techniques

### Agent Debugging

```python
# Check available tools
agent.get_available_tools()

# Verify manifests
len(agent.addon_manifests)

# Inspect tool signatures
inspect.signature(tool_function)
```

### Common Debug Points

1. **Registry Updates** - Are addon manifests being loaded?
2. **Tool Generation** - Are functions created with proper signatures?
3. **Parameter Validation** - Does B.L.A.Z.E see required parameters?
4. **WebSocket Flow** - Are messages sent correctly?

## Security and Validation

### Parameter Validation

- **Type Checking** - Pydantic validates parameter types
- **Required Parameters** - Functions enforce required vs optional
- **Enum Validation** - Options validated against manifest definitions

### WebSocket Security

- **User Isolation** - Commands tagged with username
- **Message IDs** - Unique identifiers prevent replay attacks
- **Addon Validation** - Only registered addons can receive commands

---

_This architecture document reflects the current state after comprehensive debugging and optimization of the B.L.A.Z.E parameter recognition system._
