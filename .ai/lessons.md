# Lessons

## Never let a stub be more permissive than the real API

I made `weak_sandbox.py` override `bpy.app.quit`, on the strength of a *comment*
in the upstream MCP addon recommending `bpy.app.quit()` as an alternative. The
attribute does not exist on Blender 5.1 (`hasattr(bpy.app, "quit")` → `False`).
Because the override ran in `__enter__`, **every** `execute_python` call died
before any agent code executed, and the retry loop burned both attempts on the
identical error.

The test suite passed throughout, because my stub defined
`bpy.app = SimpleNamespace(quit=...)` — inventing an attribute Blender lacks.

**Rules:**
1. Never infer an API exists from prose. Verify it —
   `blender --background --python-expr "import bpy; print(hasattr(bpy.app,'quit'))"`.
   A real Blender build lives at `~/Garage/blender-git/build_linux_release/bin/blender`
   and can run the addon directly; use it before shipping bpy-touching code.
2. Stubs must model the *narrowest* real API, and tests should cover the absent
   case explicitly (`test_cr8_script.py` now runs with and without
   `bpy.app.quit`, with a read-only `bpy.app`, and with `_op_create_function`
   missing).
3. Setup code that guards against misuse must never be able to break the feature
   it guards. `override_store` now skips attributes it cannot read or write; a
   weakened sandbox beats a tool that fails 100% of the time.


## Trace the full response path before claiming a field reaches the agent

While porting the MCP addon I added a `traceback` field to Blender-side error
responses and wrote in the plan that "the engine needs no change". Review caught
that `cr8_engine/app/blaze/command_executor.py` raises `ModelRetry` with only
`payload.data.message` — the new field was dropped one hop before the model, so
the change would have been a silent no-op.

**Rule:** when adding a field to a message that crosses a process boundary, read
the consumer at the *far* end, not just the producer. For this codebase the hop
chain is: addon handler → `registry/routing/command_executor.py` →
`ws/utils/response_manager.py` (wraps in `payload`) → Socket.IO → engine
`blaze/command_executor.py` (unwraps, and *selects* fields) → Pydantic AI. The
engine's unwrap step is lossy by design; anything not explicitly read there
never reaches B.L.A.Z.E.

## Only `description` and parameter *names* from addon_ai.json reach the model

`toolset_builder._create_dynamic_tool_function` generates a function whose
docstring is the tool's `description` and whose signature carries parameter
names and defaults — nothing else. So a tool's `usage`, `examples`, `category`,
and the manifest's `context_hints` / `agent_description` are **documentation
only**; B.L.A.Z.E never sees them. Parameter `description` and `type` are also
dropped (the generated params have no annotations).

`docs/BLAZE_ARCHITECTURE.md` describes a `_build_agent_context` that fed
manifests into the system prompt — that is not what the current
`message_processor` does, so the doc is stale on this point.

**Rule:** anything the model must know to call a tool correctly goes in the
tool's `description`, or in the agent system prompt. Writing it into `usage` and
assuming it lands is a silent failure — the tool ships, the model just never
learns the contract.

## Separately-packaged Blender addons cannot share types

`cr8_router`, `cr8_sets`, `cr8_controls`, and `cr8_script` install as independent
extensions under `bl_ext.user_default.*`. An `isinstance` check against a class
defined in one addon will not work from another without resolving the dynamic
`bl_ext` import name (the trick `registry/discovery/handler_loader.py` uses).

**Rule:** cross-addon contracts must be structural, not nominal — check for an
attribute or method, the way the registry already duck-types
`AI_COMMAND_HANDLERS`. Each addon defines its own carrier class.
