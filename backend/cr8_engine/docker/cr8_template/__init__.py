"""
cr8 Application Template for Blender.

Auto-connects to cr8_engine via WebSocket after startup.
Extensions are pre-enabled via userpref.blend baked into this template.
"""
import bpy
import logging
from bpy.app.handlers import persistent

logger = logging.getLogger(__name__)


@persistent
def _auto_connect_websocket(dummy):
    """Called after factory startup loads - extensions are registered by now."""
    def connect():
        try:
            bpy.ops.ws_handler.connect_websocket()
            logger.info("cr8 template: WebSocket connected")
        except Exception as e:
            logger.error(f"cr8 template: WebSocket connect failed: {e}")
        return None  # Don't repeat
    # Small delay to ensure Blender's main loop is fully running
    bpy.app.timers.register(connect, first_interval=1.0)


def register():
    bpy.app.handlers.load_factory_startup_post.append(_auto_connect_websocket)
    logger.info("cr8 application template registered")


def unregister():
    if _auto_connect_websocket in bpy.app.handlers.load_factory_startup_post:
        bpy.app.handlers.load_factory_startup_post.remove(_auto_connect_websocket)
    logger.info("cr8 application template unregistered")
