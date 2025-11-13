## Brief overview

Backend architecture patterns for building maintainable, scalable AI agent features with properly separated concerns and explicit workflow guidance.

## System workflow principle

**System workflows (local tools) must be explicitly documented in the system prompt.**

System workflows are multi-step operations that combine local tools (system operations we maintain). These require explicit guidance in the system prompt:

- Clear step-by-step instructions for the workflow
- When to call specific tools and in what order
- Expected outcomes at each step
- When to verify results before proceeding

**Blender addon tools are different**: They are dynamically available based on addon manifests. The AI learns appropriate usage from tool descriptions rather than explicit workflow instructions. Future addon developers can include workflow guidance in their manifests for dynamic AI teaching.

Example: Inbox asset processing workflow (system workflow)

```
When users request to download assets from their inbox:
1. Use process_inbox_assets() to download and import the assets
2. After successful download, call list_scene_objects() to verify assets are in scene
3. Once verified, ALWAYS call clear_inbox() to remove processed items
4. Provide summary confirming what was added and inbox was cleared
```

Without explicit system prompt guidance, the AI may not know when or how to orchestrate system workflows, leading to incomplete operations.

## Separation of concerns architecture

### Blender Tools (3D Operations - Dynamic)

- **Source**: Dynamically registered from any addon that provides them (via addon manifests)
- **Registration**: Via command router based on available addon manifests
- **Execution**: Called by Blender's internal command execution system
- **Capabilities**: Handle 3D scene operations (add objects, transform, animate, etc.)
- **Limitations**: Cannot access RunContext or system dependencies
- **AI Learning**: AI reads tool descriptions to determine appropriate usage
- **Workflow Guidance**: Future addon developers can include workflow sections in manifests for dynamic AI teaching

### Local Tools (System Operations - Maintained)

- **Location**: `backend/cr8_engine/app/blaze/local_tools.py`
- **Registration**: Via `@agent.tool` decorator (Pydantic AI tools)
- **Access**: Have access to RunContext and deps
- **Capabilities**: Handle system operations (inbox management, notifications, state updates)
- **Autonomy**: Can autonomously call system operations
- **Communication**: Can emit events to frontend via browser_namespace
- **Workflow Guidance**: Get explicit instructions in system prompt

**Key Principle**: Keep 3D operations (dynamic, addon-provided) separate from system operations (maintained, explicit). This prevents tight coupling, enables extensibility, and makes each tool type easier to test and maintain.

## Key technical patterns

### RunContext and Dependencies

Tools that need access to system state use RunContext:

```python
async def clear_inbox(ctx: RunContext[Dict[str, Any]]) -> str:
    browser_namespace = ctx.deps.get('browser_namespace')
    agent_instance = ctx.deps.get('agent_instance')
    # ... implementation
```

Pass dependencies via message processor:

```python
deps['browser_namespace'] = self.agent_instance.browser_namespace
deps['agent_instance'] = self.agent_instance
```

### Tool Return Values

All tools return descriptive strings for AI feedback:

- Success messages with details of what was accomplished
- Error messages with context for debugging
- Enables AI to understand tool outcomes and adjust behavior

### Message Routing

- `'agent'` route: Commands initiated by AI (autonomous workflows)
- `'direct'` route: Commands initiated by user (direct requests)

## Module organization

Create small, focused modules for specific functionality:

- `local_tools.py`: System operation tools (inbox, notifications, state)
- `message_processor.py`: Message routing and context preparation
- `command_executor.py`: Tool execution and result handling
- `agent.py`: AI agent configuration and system prompt
- `toolset_builder.py`: Dynamic tool registration

**Benefits of small modules**:

- Single responsibility principle
- Easy to locate and modify specific functionality
- Reduced cognitive load when debugging
- Clear dependencies between modules
- Easier to test individual components

## Implementation workflow

When adding a new system workflow (combining local tools):

1. **Identify the workflow steps** - What needs to happen in sequence?
2. **Separate concerns** - Which steps are 3D operations (use existing Blender tools) vs system operations (create new local tools)?
3. **Create local tools** - Implement system operation tools in `local_tools.py`
4. **Register tools** - Use `@agent.tool` decorator for local tools
5. **Update system prompt** - Add explicit workflow instructions for the system workflow
6. **Pass dependencies** - Ensure tools have access to needed context via deps
7. **Test workflow** - Verify AI calls tools in correct sequence

When using existing Blender addon tools:

1. **Discover available tools** - Check addon manifests for available tools
2. **Read tool descriptions** - Understand tool capabilities from descriptions
3. **Compose requests** - Let AI determine appropriate tool usage based on descriptions
4. **No explicit workflow needed** - Blender tools are self-documenting via descriptions

## Benefits

### Maintainability

- Changes isolated to specific modules
- Clear separation between tool types
- Easy to understand tool responsibilities
- Reduced side effects from modifications

### Debugging

- Trace issues to specific tool or module
- Isolated test cases for individual tools
- Clear error messages from tool return values
- System prompt guides expected behavior

### Scalability

- New features added without affecting existing code
- Tool registration pattern supports unlimited tools
- Modular structure supports team development
- Clear patterns for new developers to follow

## Example: Inbox Clearing Implementation

The inbox clearing feature demonstrates all these principles:

1. **System workflow in prompt**: Explicit instructions for download → verify → clear sequence
2. **Separated concerns**:
   - Blender tool: `process_inbox_assets()` (3D import - uses tool description)
   - Local tool: `clear_inbox()` (system operation - explicit workflow)
3. **Small modules**:
   - `local_tools.py` for clear_inbox
   - `message_processor.py` for context
   - `agent.py` for workflow orchestration
4. **Dependencies passed**: browser_namespace and agent_instance available to clear_inbox
5. **Tool returns feedback**: "Inbox cleared successfully for {username}"
6. **AI autonomous**: System prompt guides AI to orchestrate the workflow

This pattern can be replicated for any multi-step system workflow combining local tools.

## Future: Manifest-Based Workflow Guidance

As the addon ecosystem grows, addon developers can include workflow guidance in their manifests:

- Addon manifests can define workflow sections alongside tool definitions
- AI dynamically learns tool usage patterns from manifests
- Keeps system prompt clean while enabling extensible tool ecosystems
- Addon developers teach AI how to use their tools effectively
- System remains flexible as new addons are added

This approach scales the system beyond hardcoded workflows while maintaining explicit guidance where needed.
