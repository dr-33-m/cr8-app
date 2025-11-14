"""
Handlers package for Blender Controls addon
Contains all command handlers organized by functionality
"""

from .animation_handlers import (
    handle_frame_jump_start,
    handle_frame_jump_end,
    handle_keyframe_jump_prev,
    handle_keyframe_jump_next,
    handle_animation_play,
    handle_animation_play_reverse,
    handle_animation_pause
)

from .viewport_handlers import (
    handle_viewport_set_solid,
    handle_viewport_set_rendered,
    handle_get_viewport_screenshot
)

from .navigation_handlers import (
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

__all__ = [
    # Animation handlers
    'handle_frame_jump_start',
    'handle_frame_jump_end',
    'handle_keyframe_jump_prev',
    'handle_keyframe_jump_next',
    'handle_animation_play',
    'handle_animation_play_reverse',
    'handle_animation_pause',
    # Viewport handlers
    'handle_viewport_set_solid',
    'handle_viewport_set_rendered',
    'handle_get_viewport_screenshot',
    # Navigation handlers
    'handle_orbit_left',
    'handle_orbit_right',
    'handle_orbit_up',
    'handle_orbit_down',
    'handle_pan_left',
    'handle_pan_right',
    'handle_pan_up_forward',
    'handle_pan_down_backward',
    'handle_zoom_in',
    'handle_zoom_out',
]
