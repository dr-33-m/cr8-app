# Blaze Script

Python execution for B.L.A.Z.E. When no dedicated tool covers a request, the
agent writes `bpy` code instead of the capability simply not existing.

The execution substrate is adapted from [Blender Lab's official MCP add-on][mcp]
(`blender_mcp` 1.0.0, GPL-3.0-or-later — same licence as this addon):
`capture_output.py` is vendored unchanged, `weak_sandbox.py` keeps the mechanism
with a cr8-extended blocklist, and `executor.py` follows upstream's code
contract while emitting cr8's response envelope.

[mcp]: https://www.blender.org/lab/mcp-server/

## The code contract

Agent-authored code follows three rules, documented for the model in
`addon_ai.json`:

1. **Return values** — assign a dict to `result`. Non-serializable values (a
   `bpy.types.Object`, say) degrade to their repr rather than failing the call.
2. **Debugging** — `print()` output is captured into `stdout`, as is anything
   Blender prints. Exceptions return the full traceback so the agent can
   correct itself on retry.
3. **Long operations** — code runs on Blender's main thread. To start slow work
   (render, bake, simulation), define a no-argument `check_is_finished` that
   returns `None` while pending and a dict when done. `cr8_router` polls it on a
   timer and replies against the original `message_id`; the viewport stays
   responsive. When it is defined, `result` is ignored.

## Guardrails

`weak_sandbox.py` blocks operators that would end the session or discard the
user's project — `wm.quit_blender`, the `read_factory_*` / `read_userpref`
family, `wm.read_homefile`, `wm.open_mainfile`, `wm.save_as_mainfile` — plus
`sys.exit` and `bpy.app.quit`. Each rejection explains itself and suggests an
alternative.

This is deliberately **not** a security boundary; upstream's rule of thumb is to
block only what is guaranteed to break things. The trust model is unchanged: one
isolated instance per user, which B.L.A.Z.E already drives.

Set `CR8_ALLOW_CODE_EXEC=0` to refuse execution on a deployment. The tool stays
visible and returns a `CODE_EXECUTION_DISABLED` error, which is clearer to the
agent than the tool vanishing.

## Packaging

```bash
python package_addon.py            # → dist/cr8_script_v1.0.0.zip
python package_addon.py --validate # structure check only
```

Requires `cr8_router` installed and enabled — it provides discovery, routing,
and the deferred-response timer.
