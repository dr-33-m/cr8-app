"""
Blaze Script Addon - Python execution for AI agents

Gives B.L.A.Z.E an escape hatch: when no dedicated tool covers a request, it can
write bpy code directly instead of the capability simply not existing. The
execution substrate (the `result` dict contract, the weak sandbox, the stdout
tee, the deferred-response hook) is adapted from Blender Lab's official MCP
add-on, which is licensed GPL-3.0-or-later like this one.

Caveats worth knowing before extending this:

- Code runs on Blender's main thread, inside the router's command drainer. A
  blocking loop freezes Blender *and* the WebRTC viewport stream. Anything slow
  must define `check_is_finished` so the response is deferred (see executor.py
  and cr8_router/registry/routing/deferred.py).
- The sandbox in weak_sandbox.py is a slap on the wrist, not a security
  boundary. The trust model is unchanged: one isolated instance per user, and
  B.L.A.Z.E already drives it.
- Set CR8_ALLOW_CODE_EXEC=0 to refuse execution on a given deployment.
"""

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bl_info = {
    "name": "Blaze Script",
    "author": "Cr8-xyz <thamsanqa.dev@gmail.com>",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "AI Integration Only",
    "description": "Python execution for AI agents",
    "warning": "Executes agent-authored Python inside Blender",
    "wiki_url": "https://code.cr8-xyz.art/Cr8-xyz/cr8-app",
    "category": "Development",
}

from .handlers.script_handlers import handle_execute_python

# Export command handlers for the AI router
AI_COMMAND_HANDLERS = {
    'execute_python': handle_execute_python,
}


def register():
    """Register the Blaze Script addon"""
    try:
        logger.info("Registering Blaze Script addon...")
        logger.info(
            f"Script addon registered with {len(AI_COMMAND_HANDLERS)} command handlers")
    except Exception as e:
        logger.error(f"Failed to register Script addon: {str(e)}")
        raise


def unregister():
    """Unregister the Blaze Script addon"""
    try:
        logger.info("Unregistering Blaze Script addon...")
        logger.info("Script addon unregistered")
    except Exception as e:
        logger.error(f"Failed to unregister Script addon: {str(e)}")


if __name__ == "__main__":
    register()
