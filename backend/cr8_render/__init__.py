"""
Cr8 Render Addon - Image and (later) video output for AI agents

Owns the output side of the pipeline: render profiles, camera selection,
resolution, and uploading finished frames to cloud storage. Kept separate from
the router so the router stays routing-only, and so rendering is reachable by
B.L.A.Z.E through the normal addon manifest like any other creative capability.
"""

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bl_info = {
    "name": "Cr8 Render",
    "author": "Cr8-xyz <thamsanqa.dev@gmail.com>",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "Render",
    "description": "Image rendering and cloud output for AI agents",
    "warning": "",
    "wiki_url": "https://code.cr8-xyz.art/Cr8-xyz/cr8-app",
    "category": "Render",
}

from .handlers.render_handlers import handle_render_image

# Exported for the AI router's registry — the keys here must match the tool
# names in addon_ai.json, or the command resolves to COMMAND_NOT_FOUND.
AI_COMMAND_HANDLERS = {
    'render_image': handle_render_image,
}


def register():
    """Register the Cr8 Render addon"""
    try:
        logger.info("Registering Cr8 Render addon...")
        logger.info(
            f"Render addon registered with {len(AI_COMMAND_HANDLERS)} command handlers")
    except Exception as e:
        logger.error(f"Failed to register Render addon: {str(e)}")
        raise


def unregister():
    """Unregister the Cr8 Render addon"""
    try:
        logger.info("Unregistering Cr8 Render addon...")
    except Exception as e:
        logger.error(f"Failed to unregister Render addon: {str(e)}")


if __name__ == "__main__":
    register()
