"""
Scene spatial B.L.A.Z.E integration functions.

Provides functions for querying scene objects, transforming objects,
and managing object selection and focus.
"""

import json
import logging
from typing import Optional

from ... import scene_spatial

logger = logging.getLogger(__name__)


# ============================================================================
# Scene Querying Functions
# ============================================================================


def list_scene_objects() -> list:
    """Get list of all objects in the current scene."""
    try:
        return scene_spatial.list_scene_objects()
    except Exception as e:
        logger.error(f"List scene objects failed: {e}")
        return [{"error": f"Failed to list objects: {str(e)}"}]


def get_objects_by_type(asset_type: str = "all") -> str:
    """Filter objects in scene by type."""
    try:
        result = scene_spatial.get_objects_by_type(asset_type)
        return json.dumps({
            "success": True,
            "message": result,
            "operation": "get_objects_by_type",
            "parameters": {"asset_type": asset_type},
        }, indent=2)
    except Exception as e:
        logger.error(f"Get objects by type failed: {e}")
        return json.dumps({"success": False, "message": f"Failed to filter objects: {str(e)}"})


# ============================================================================
# Transformation Functions
# ============================================================================


def transform_resize(
    value_x: float = 1.0,
    value_y: float = 1.0,
    value_z: float = 1.0,
    constraint_x: bool = False,
    constraint_y: bool = False,
    constraint_z: bool = False,
    snap: bool = False,
    snap_target: str = "CLOSEST",
) -> str:
    """Resize/scale selected objects."""
    try:
        result = scene_spatial.transform_resize(
            value_x=value_x,
            value_y=value_y,
            value_z=value_z,
            constraint_x=constraint_x,
            constraint_y=constraint_y,
            constraint_z=constraint_z,
            snap=snap,
            snap_target=snap_target,
        )
        return json.dumps({
            "success": True,
            "message": result,
            "operation": "transform_resize",
        }, indent=2)
    except Exception as e:
        logger.error(f"Transform resize failed: {e}")
        return json.dumps({"success": False, "message": f"Failed to resize objects: {str(e)}"})


def transform_translate(
    value_x: float = 0.0,
    value_y: float = 0.0,
    value_z: float = 0.0,
    constraint_x: bool = False,
    constraint_y: bool = False,
    constraint_z: bool = False,
    snap: bool = False,
    snap_target: str = "CLOSEST",
) -> str:
    """Translate/move selected objects."""
    try:
        result = scene_spatial.transform_translate(
            value_x=value_x,
            value_y=value_y,
            value_z=value_z,
            constraint_x=constraint_x,
            constraint_y=constraint_y,
            constraint_z=constraint_z,
            snap=snap,
            snap_target=snap_target,
        )
        return json.dumps({
            "success": True,
            "message": result,
            "operation": "transform_translate",
        }, indent=2)
    except Exception as e:
        logger.error(f"Transform translate failed: {e}")
        return json.dumps({"success": False, "message": f"Failed to translate objects: {str(e)}"})


def transform_rotate(
    value_x: float = 0.0,
    value_y: float = 0.0,
    value_z: float = 0.0,
    constraint_x: bool = False,
    constraint_y: bool = False,
    constraint_z: bool = False,
    snap: bool = False,
    snap_target: str = "CLOSEST",
) -> str:
    """Rotate selected objects to absolute rotation on all axes."""
    try:
        result = scene_spatial.transform_rotate(
            value_x=value_x,
            value_y=value_y,
            value_z=value_z,
            constraint_x=constraint_x,
            constraint_y=constraint_y,
            constraint_z=constraint_z,
            snap=snap,
            snap_target=snap_target,
        )
        return json.dumps({
            "success": True,
            "message": result,
            "operation": "transform_rotate",
        }, indent=2)
    except Exception as e:
        logger.error(f"Transform rotate failed: {e}")
        return json.dumps({"success": False, "message": f"Failed to rotate objects: {str(e)}"})


# ============================================================================
# Object Management Functions
# ============================================================================


def set_active_object(object_name: str) -> str:
    """Make an object the active object in the scene."""
    try:
        result = scene_spatial.set_active_object(object_name=object_name)
        return json.dumps({
            "success": True,
            "message": result,
            "operation": "set_active_object",
        }, indent=2)
    except Exception as e:
        logger.error(f"Set active object failed: {e}")
        return json.dumps({"success": False, "message": f"Failed to set active object: {str(e)}"})


def focus_on_active_object() -> str:
    """Focus the 3D view on the currently active object."""
    try:
        result = scene_spatial.focus_on_active_object()
        return json.dumps({
            "success": True,
            "message": result,
            "operation": "focus_on_active_object",
        }, indent=2)
    except Exception as e:
        logger.error(f"Focus on active object failed: {e}")
        return json.dumps({"success": False, "message": f"Failed to focus on active object: {str(e)}"})


def select_object(object_name: str, deselect_others: bool = True) -> str:
    """Select an object in the scene."""
    try:
        result = scene_spatial.select_object(
            object_name=object_name,
            deselect_others=deselect_others,
        )
        return json.dumps({
            "success": True,
            "message": result,
            "operation": "select_object",
        }, indent=2)
    except Exception as e:
        logger.error(f"Select object failed: {e}")
        return json.dumps({"success": False, "message": f"Failed to select object: {str(e)}"})


def delete_object(object_name: str) -> str:
    """Delete an object from the scene."""
    try:
        result = scene_spatial.handle_delete_object(object_name=object_name)
        return json.dumps({
            "success": True,
            "message": result,
            "operation": "delete_object",
        }, indent=2)
    except Exception as e:
        logger.error(f"Delete object failed: {e}")
        return json.dumps({"success": False, "message": f"Failed to delete object: {str(e)}"})
