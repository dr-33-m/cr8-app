"""
Blender Controls Addon - Animation, viewport, and navigation controls
Provides scene manipulation and viewport control capabilities for AI agents
"""

import bpy
import logging
from .handlers import animation_handlers, viewport_handlers, navigation_handlers

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bl_info = {
    "name": "Blaze Controls",
    "author": "Cr8-xyz <thamsanqa.dev@gmail.com>",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Tools",
    "description": "Animation, viewport, and navigation controls for AI agents",
    "warning": "",
    "wiki_url": "https://code.streetcrisis.online/Cr8-xyz/cr8-app",
    "category": "Development",
}

# Import all command handlers from their respective modules
from .handlers.animation_handlers import (
    handle_frame_jump_start,
    handle_frame_jump_end,
    handle_keyframe_jump_prev,
    handle_keyframe_jump_next,
    handle_animation_play,
    handle_animation_play_reverse,
    handle_animation_pause
)

from .handlers.viewport_handlers import (
    handle_viewport_set_solid,
    handle_viewport_set_rendered,
    handle_get_viewport_screenshot
)

from .handlers.navigation_handlers import (
    handle_orbit_left,
    handle_orbit_right,
    handle_orbit_up,
    handle_orbit_down,
    handle_pan_left,
    handle_pan_right,
    handle_pan_up_forward,
    handle_pan_down_backward,
    handle_zoom_in,
    handle_zoom_out
)

# Export all command handlers for the AI router
AI_COMMAND_HANDLERS = {
    # Animation controls
    'frame_jump_start': handle_frame_jump_start,
    'frame_jump_end': handle_frame_jump_end,
    'keyframe_jump_prev': handle_keyframe_jump_prev,
    'keyframe_jump_next': handle_keyframe_jump_next,
    'animation_play': handle_animation_play,
    'animation_play_reverse': handle_animation_play_reverse,
    'animation_pause': handle_animation_pause,
    # Viewport controls
    'viewport_set_solid': handle_viewport_set_solid,
    'viewport_set_rendered': handle_viewport_set_rendered,
    'get_viewport_screenshot': handle_get_viewport_screenshot,
    # 3D Navigation controls
    'orbit_left': handle_orbit_left,
    'orbit_right': handle_orbit_right,
    'orbit_up': handle_orbit_up,
    'orbit_down': handle_orbit_down,
    'pan_left': handle_pan_left,
    'pan_right': handle_pan_right,
    'pan_up_forward': handle_pan_up_forward,
    'pan_down_backward': handle_pan_down_backward,
    'zoom_in': handle_zoom_in,
    'zoom_out': handle_zoom_out,
}


def register():
    """Register the Blender Controls addon"""
    try:
        logger.info("Registering Blender Controls addon...")
        # Addon registration logic would go here if needed
        logger.info(f"Controls addon registered with {len(AI_COMMAND_HANDLERS)} command handlers")
    except Exception as e:
        logger.error(f"Failed to register Controls addon: {str(e)}")
        raise


def unregister():
    """Unregister the Blender Controls addon"""
    try:
        logger.info("Unregistering Blender Controls addon...")
        # Addon unregistration logic would go here if needed
        logger.info("Controls addon unregistered")
    except Exception as e:
        logger.error(f"Failed to unregister Controls addon: {str(e)}")


if __name__ == "__main__":
    register()
