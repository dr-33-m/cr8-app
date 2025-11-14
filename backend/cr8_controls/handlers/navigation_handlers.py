"""
Navigation Control Handlers
Handles all 3D navigation commands for the Blender Controls addon
"""

import bpy
import logging
from ..utils.view3d_context import ensure_view3d_context, pan_view_manual

logger = logging.getLogger(__name__)


def handle_orbit_left() -> dict:
    """Orbit view to the left"""
    try:
        context = ensure_view3d_context()
        if context:
            with bpy.context.temp_override(**context):
                bpy.ops.view3d.view_orbit(type='ORBITLEFT')
        else:
            return {
                "status": "error",
                "message": "No VIEW_3D region found",
                "error_code": "NAVIGATION_ERROR"
            }

        return {
            "status": "success",
            "message": "Orbited view left",
            "data": {"navigation_action": "orbit_left"}
        }
    except Exception as e:
        logger.error(f"Error orbiting left: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to orbit left: {str(e)}",
            "error_code": "NAVIGATION_ERROR"
        }


def handle_orbit_right() -> dict:
    """Orbit view to the right"""
    try:
        context = ensure_view3d_context()
        if context:
            with bpy.context.temp_override(**context):
                bpy.ops.view3d.view_orbit(type='ORBITRIGHT')
        else:
            return {
                "status": "error",
                "message": "No VIEW_3D region found",
                "error_code": "NAVIGATION_ERROR"
            }

        return {
            "status": "success",
            "message": "Orbited view right",
            "data": {"navigation_action": "orbit_right"}
        }
    except Exception as e:
        logger.error(f"Error orbiting right: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to orbit right: {str(e)}",
            "error_code": "NAVIGATION_ERROR"
        }


def handle_orbit_up() -> dict:
    """Orbit view up"""
    try:
        context = ensure_view3d_context()
        if context:
            with bpy.context.temp_override(**context):
                bpy.ops.view3d.view_orbit(type='ORBITUP')
        else:
            return {
                "status": "error",
                "message": "No VIEW_3D region found",
                "error_code": "NAVIGATION_ERROR"
            }

        return {
            "status": "success",
            "message": "Orbited view up",
            "data": {"navigation_action": "orbit_up"}
        }
    except Exception as e:
        logger.error(f"Error orbiting up: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to orbit up: {str(e)}",
            "error_code": "NAVIGATION_ERROR"
        }


def handle_orbit_down() -> dict:
    """Orbit view down"""
    try:
        context = ensure_view3d_context()
        if context:
            with bpy.context.temp_override(**context):
                bpy.ops.view3d.view_orbit(type='ORBITDOWN')
        else:
            return {
                "status": "error",
                "message": "No VIEW_3D region found",
                "error_code": "NAVIGATION_ERROR"
            }

        return {
            "status": "success",
            "message": "Orbited view down",
            "data": {"navigation_action": "orbit_down"}
        }
    except Exception as e:
        logger.error(f"Error orbiting down: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to orbit down: {str(e)}",
            "error_code": "NAVIGATION_ERROR"
        }


def handle_pan_left(amount: float = 0.5) -> dict:
    """Pan view to the left"""
    try:
        # Primary approach: Manual pan (reliable)
        pan_view_manual('PANLEFT', amount)

        return {
            "status": "success",
            "message": f"Panned view left by {amount}",
            "data": {"navigation_action": "pan_left", "amount": amount}
        }
    except Exception as e:
        logger.error(f"Error panning left: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to pan left: {str(e)}",
            "error_code": "NAVIGATION_ERROR"
        }


def handle_pan_right(amount: float = 0.5) -> dict:
    """Pan view to the right"""
    try:
        # Primary approach: Manual pan (reliable)
        pan_view_manual('PANRIGHT', amount)


        return {
            "status": "success",
            "message": f"Panned view right by {amount}",
            "data": {"navigation_action": "pan_right", "amount": amount}
        }
    except Exception as e:
        logger.error(f"Error panning right: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to pan right: {str(e)}",
            "error_code": "NAVIGATION_ERROR"
        }


def handle_pan_up_forward(direction: str, amount: float = 0.5) -> dict:
    """Pan view up or forward"""
    valid_directions = ['PANUP', 'PANFORWARD']
    if direction not in valid_directions:
        return {
            "status": "error",
            "message": f"Invalid direction for up/forward pan. Must be one of: {', '.join(valid_directions)}",
            "error_code": "INVALID_DIRECTION"
        }

    try:
        # Primary approach: Manual pan (reliable)
        pan_view_manual(direction, amount)

        direction_name = "up" if direction == 'PANUP' else "forward"

        return {
            "status": "success",
            "message": f"Panned view {direction_name} by {amount}",
            "data": {"navigation_action": f"pan_{direction_name}", "direction": direction, "amount": amount}
        }
    except Exception as e:
        logger.error(f"Error panning {direction}: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to pan {direction}: {str(e)}",
            "error_code": "NAVIGATION_ERROR"
        }


def handle_pan_down_backward(direction: str, amount: float = 0.5) -> dict:
    """Pan view down or backward"""
    valid_directions = ['PANDOWN', 'PANBACK']
    if direction not in valid_directions:
        return {
            "status": "error",
            "message": f"Invalid direction for down/backward pan. Must be one of: {', '.join(valid_directions)}",
            "error_code": "INVALID_DIRECTION"
        }

    try:
        # Primary approach: Manual pan (reliable)
        pan_view_manual(direction, amount)

        direction_name = "down" if direction == 'PANDOWN' else "backward"

        return {
            "status": "success",
            "message": f"Panned view {direction_name} by {amount}",
            "data": {"navigation_action": f"pan_{direction_name}", "direction": direction, "amount": amount}
        }
    except Exception as e:
        logger.error(f"Error panning {direction}: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to pan {direction}: {str(e)}",
            "error_code": "NAVIGATION_ERROR"
        }


def handle_zoom_in() -> dict:
    """Zoom in to the viewport"""
    try:
        context = ensure_view3d_context()
        if context:
            with bpy.context.temp_override(**context):
                bpy.ops.view3d.zoom(delta=1)
        else:
            return {
                "status": "error",
                "message": "No VIEW_3D region found",
                "error_code": "NAVIGATION_ERROR"
            }

        return {
            "status": "success",
            "message": "Zoomed in",
            "data": {"navigation_action": "zoom_in"}
        }
    except Exception as e:
        logger.error(f"Error zooming in: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to zoom in: {str(e)}",
            "error_code": "NAVIGATION_ERROR"
        }


def handle_zoom_out() -> dict:
    """Zoom out from the viewport"""
    try:
        context = ensure_view3d_context()
        if context:
            with bpy.context.temp_override(**context):
                bpy.ops.view3d.zoom(delta=-1)
        else:
            return {
                "status": "error",
                "message": "No VIEW_3D region found",
                "error_code": "NAVIGATION_ERROR"
            }

        return {
            "status": "success",
            "message": "Zoomed out",
            "data": {"navigation_action": "zoom_out"}
        }
    except Exception as e:
        logger.error(f"Error zooming out: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to zoom out: {str(e)}",
            "error_code": "NAVIGATION_ERROR"
        }
