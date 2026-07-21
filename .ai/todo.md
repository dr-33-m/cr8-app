# Port Blender-org MCP addon capabilities into Blaze

Source: `~/Garage/blender_mcp-1.0.0` (Blender Lab official MCP addon, GPL-3.0-or-later).
Plan: `~/.claude/plans/inside-garage-i-just-cozy-hartmanis.md`

## Part B — cr8_router deferred results

- [x] `cr8_router/registry/routing/deferred.py` — port of `deferred_tool.py`, keyed on message_id
- [x] Export from `registry/routing/__init__.py`
- [x] `command_executor.py` — pass deferred results through untouched
- [x] `command_handlers.py` — register deferred, suppress immediate response
- [x] `event_handlers.py` — drop pending deferred work on disconnect

## Part C — Router hardening

- [x] `command_executor.py` — full traceback in error responses
- [x] `command_executor.py` — JSON-serializability guard on all handler results
- [x] `event_handlers.py` — idle backoff for `_drain_command_queue`
- [x] **(added during review)** engine `command_executor.py` — surface traceback/stdout in `ModelRetry`

## Part A — New cr8_script addon

- [x] `capture_output.py` (port)
- [x] `weak_sandbox.py` (port + cr8 blocklist)
- [x] `executor.py` (port of `_execute_code`, cr8 response envelope)
- [x] `handlers/script_handlers.py` — `handle_execute_python` + kill switch
- [x] `__init__.py`, `blender_manifest.toml`, `addon_ai.json`, `package_addon.py`, `README.md`

## Part D — Blaze prompt + packaging

- [x] `cr8_engine/app/blaze/agent.py` — system prompt guidance
- [x] `docker/build.sh` + `docker/Dockerfile` — fourth addon zip

## Review

**What shipped.** B.L.A.Z.E gains `execute_python` (a fallback for anything no
dedicated tool covers), `cr8_router` gains deferred responses for long-running
work, and the router's error/serialization handling got hardened for all addons.

**Design decisions that departed from the plan:**

1. *Duck typing instead of `isinstance` for deferred results.* `cr8_script` and
   `cr8_router` install as separate extensions (`bl_ext.user_default.*`), so a
   shared `DeferredResult` base class would need a fragile cross-addon import.
   The router instead checks for a callable `check_is_finished` attribute, which
   mirrors upstream's own namespace convention and matches how
   `AI_COMMAND_HANDLERS` is already a duck-typed contract. Each addon defines
   its own carrier class. Covered by the `ForeignDeferred` test case.

2. *Kill switch inside the handler, not at registration.* `scanner.py` builds the
   agent's tool list from `addon_ai.json` on disk regardless of which handlers
   exist, so withholding the handler would leave a phantom tool failing with an
   opaque `NO_HANDLERS`. The handler returns `CODE_EXECUTION_DISABLED` instead.

3. *Engine-side change the plan said would not be needed.* The plan asserted the
   engine needed no edits. Review found `execute_addon_command` raises
   `ModelRetry` with only `payload.data.message`, silently dropping the new
   `traceback` field — which would have made Part C a no-op for the agent.
   Added `_format_failure` to append traceback/stdout/stderr, de-duplicating
   when the handler already put the trace in `message` (as `execute_python`
   does).

**Verification.** 19 executor/sandbox checks, 23 deferred-poller checks, 13
router-hardening checks, 4 failure-formatter checks — all passing against
stubbed `bpy`. Manifest validates; addon packages cleanly. Not yet run inside
real Blender — see "How to test" for the manual smoke tests.

**Known caveats (documented in `cr8_script/__init__.py`):** code runs on the main
thread so a blocking loop freezes the viewport (`check_is_finished` is the escape
hatch); `CaptureOutput` swaps `sys.stdout` process-wide so concurrent Socket.IO
logs can bleed into the buffer; the sandbox is a slap on the wrist, not a
security boundary.
