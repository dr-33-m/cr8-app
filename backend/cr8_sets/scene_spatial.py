import bpy
import mathutils

# The rotation_mode values that actually drive rotation_euler. An object in any
# other mode ('QUATERNION', 'AXIS_ANGLE') ignores rotation_euler entirely — reads
# return whatever stale values happen to be sitting there, and writes do nothing.
EULER_MODES = {'XYZ', 'XZY', 'YXZ', 'YZX', 'ZXY', 'ZYX'}


def _resolve_target(object_name: str = ""):
    """Target the named object, falling back to the active object."""
    if object_name:
        return bpy.data.objects.get(object_name)
    return bpy.context.active_object


def _effective_euler(obj) -> list:
    """
    Rotation as an XYZ euler whatever the object's rotation_mode is.

    Reading obj.rotation_euler directly is wrong for anything the glTF importer
    produced: it sets rotation_mode='QUATERNION' on every object it creates, so
    rotation_euler is stale and usually (0, 0, 0) — which is why the transform
    sliders always opened at zero for Polyhaven assets.
    """
    if obj.rotation_mode in EULER_MODES:
        return list(obj.rotation_euler)
    if obj.rotation_mode == 'QUATERNION':
        return list(obj.rotation_quaternion.to_euler('XYZ'))
    # AXIS_ANGLE is stored as (angle, x, y, z)
    axis_angle = obj.rotation_axis_angle
    return list(mathutils.Quaternion(axis_angle[1:], axis_angle[0]).to_euler('XYZ'))


def list_scene_objects() -> list:
    """
    AI tool: Get detailed list of all objects in the current scene.
    
    Returns:
        List of dictionaries with object name, type, and basic transform info
    """
    try:
        objects_info = []

        # Enumerate objects actually linked to the current scene, NOT
        # bpy.data.objects. The latter is every object datablock in the file,
        # including ones deleted from the scene that still linger in blend data
        # (a fake user, or linked in another scene/collection). Those show up in
        # the browser's object list as un-selectable ghosts that never clear on
        # refresh — exactly the "deleted objects still listed" bug. An empty
        # scene has no such lingering datablocks, which is why it looked fine.
        for obj in bpy.context.scene.objects:
            obj_info = {
                'name': obj.name,
                'type': obj.type,
                'visible': obj.visible_get(),
                'selected': obj.select_get(),
                'active': obj == bpy.context.active_object,
                'location': list(obj.location),
                'rotation': _effective_euler(obj),
                'rotation_mode': obj.rotation_mode,
                'scale': list(obj.scale)
            }
            
            objects_info.append(obj_info)
        
        return objects_info
        
    except Exception as e:
        return [{'error': f"Error listing objects: {str(e)}"}]


def get_objects_by_type(object_type: str) -> list:
    """
    AI tool: Get all objects of a specific type.
    
    Args:
        object_type: Blender object type (e.g., 'MESH', 'LIGHT', 'CAMERA', etc.)
    
    Returns:
        List of object names of the specified type
    """
    try:
        objects = [obj.name for obj in bpy.data.objects if obj.type == object_type.upper()]
        return objects
        
    except Exception as e:
        return [f"Error filtering objects: {str(e)}"]


def transform_resize(value_x: float = 1.0, value_y: float = 1.0, value_z: float = 1.0,
                    constraint_x: bool = False, constraint_y: bool = False, constraint_z: bool = False,
                    snap: bool = False, snap_target: str = 'CLOSEST', object_name: str = "") -> dict:
    """
    AI tool: Set an object's absolute scale on each axis.

    Args:
        value_x, value_y, value_z: Absolute scale per axis (1.0 = the object's
            original size). These are not multipliers — passing 2.0 twice leaves
            the object at 2x, not 4x.
        constraint_x, constraint_y, constraint_z: Apply only the axes flagged
            True. Leave all False to apply all three.
        snap: Unused. Snapping has no meaning for an absolute scale.
        snap_target: Unused, kept for signature compatibility.
        object_name: Object to scale. Omit to use the active object.

    Returns:
        Dict with operation result
    """
    try:
        obj = _resolve_target(object_name)
        if obj is None:
            return {
                'success': False,
                'error': f'Object "{object_name}" not found' if object_name else 'No active object'
            }

        # This used to call bpy.ops.transform.resize, which *multiplies* the
        # current scale rather than setting it. Every caller — the UI slider and
        # the agent alike — passes absolute values, so the values compounded:
        # dragging the slider to 1.4 left the object at 2.4x, resetting to 1.0
        # did nothing at all (x1), and dragging back down to 1.0 grew it further
        # still. Assigning obj.scale makes this absolute and idempotent, matching
        # transform_translate and transform_rotate, and scales the object about
        # its own origin instead of the scene's pivot point.
        constraints = (constraint_x, constraint_y, constraint_z)
        values = (value_x, value_y, value_z)
        # Blender's constraint_axis convention: all-False means "unconstrained".
        apply_all = not any(constraints)

        for axis, (constrained, value) in enumerate(zip(constraints, values)):
            if apply_all or constrained:
                obj.scale[axis] = value

        obj.update_tag(refresh={'OBJECT'})
        bpy.context.view_layer.update()

        applied = tuple(round(v, 4) for v in obj.scale)
        return {'success': True, 'message': f'Set scale of "{obj.name}" to {applied}'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def transform_translate(value_x: float = 0.0, value_y: float = 0.0, value_z: float = 0.0,
                       constraint_x: bool = False, constraint_y: bool = False, constraint_z: bool = False,
                       snap: bool = False, snap_target: str = 'CLOSEST', object_name: str = "") -> dict:
    """
    AI tool: Move an object to an absolute position.

    Args:
        value_x, value_y, value_z: Absolute position coordinates
        constraint_x, constraint_y, constraint_z: Lock transformation to specific axes
        snap: Enable snapping
        snap_target: Snap target ('CLOSEST', 'CENTER', 'MEDIAN', 'ACTIVE')
        object_name: Object to move. Omit to use the active object.

    Returns:
        Dict with operation result
    """
    try:
        # Operator-based, so it acts on the selection — make the requested object
        # the selection first rather than trusting whatever happened to be active.
        if object_name:
            select_result = set_active_object(object_name)
            if not select_result['success']:
                return select_result

        if bpy.context.active_object:
            # Calculate relative movement needed to reach absolute position
            current_loc = bpy.context.active_object.location
            delta_x = value_x - current_loc.x
            delta_y = value_y - current_loc.y  
            delta_z = value_z - current_loc.z
            
            # Only translate if there's actually a difference
            if abs(delta_x) > 0.001 or abs(delta_y) > 0.001 or abs(delta_z) > 0.001:
                bpy.ops.transform.translate(
                    value=(delta_x, delta_y, delta_z),
                    constraint_axis=(constraint_x, constraint_y, constraint_z),
                    snap=snap,
                    snap_target=snap_target
                )
            return {'success': True, 'message': f'Set object position to ({value_x}, {value_y}, {value_z})'}
        else:
            return {'success': False, 'error': 'No active object'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def transform_rotate(value_x: float = 0.0, value_y: float = 0.0, value_z: float = 0.0,
                    constraint_x: bool = False, constraint_y: bool = False, constraint_z: bool = False,
                    snap: bool = False, snap_target: str = 'CLOSEST', object_name: str = "") -> dict:
    """
    AI tool: Rotate an object to an absolute rotation on all axes.

    Args:
        value_x, value_y, value_z: Absolute rotation in radians per axis
        constraint_x, constraint_y, constraint_z: Apply only the axes flagged
            True. Leave all False to apply all three.
        snap: Unused. Snapping has no meaning for an absolute rotation.
        snap_target: Unused, kept for signature compatibility.
        object_name: Object to rotate. Omit to use the active object.

    Returns:
        Dict with operation result
    """
    try:
        obj = _resolve_target(object_name)
        if obj is None:
            return {
                'success': False,
                'error': f'Object "{object_name}" not found' if object_name else 'No active object'
            }

        # Blender only honours rotation_euler when rotation_mode is one of the
        # euler orders. The glTF importer — which every Polyhaven model goes
        # through — sets rotation_mode='QUATERNION', so writing rotation_euler on
        # those objects did nothing at all. Assigning rotation_mode converts the
        # existing rotation into the new representation (BKE_rotMode_change_values),
        # so the object does not jump when we switch it over.
        converted_from = ""
        if obj.rotation_mode not in EULER_MODES:
            converted_from = obj.rotation_mode
            obj.rotation_mode = 'XYZ'

        # constraint_* was declared but never honoured here, so "rotate only on Z"
        # silently rewrote all three axes. Same convention as transform_resize:
        # all-False means unconstrained.
        constraints = (constraint_x, constraint_y, constraint_z)
        values = (value_x, value_y, value_z)
        apply_all = not any(constraints)

        for axis, (constrained, value) in enumerate(zip(constraints, values)):
            if apply_all or constrained:
                obj.rotation_euler[axis] = value

        # Update the object to reflect changes
        obj.update_tag(refresh={'OBJECT'})
        bpy.context.view_layer.update()

        applied = tuple(round(v, 4) for v in obj.rotation_euler)
        message = f'Set rotation of "{obj.name}" to {applied} radians'
        if converted_from:
            message += f' (rotation mode converted from {converted_from} to XYZ)'
        return {'success': True, 'message': message}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def focus_on_active_object() -> dict:
    """
    AI tool: Focus the 3D view on the currently active object.
    
    Returns:
        Dict with operation result
    """
    try:
        # Check if there's an active object
        if bpy.context.active_object is None:
            return {'success': False, 'error': 'No active object to focus on'}
        
        # Get VIEW_3D context
        view3d_context = ensure_view3d_context()
        if view3d_context is None:
            return {'success': False, 'error': 'No 3D viewport found'}
        
        # Override context and focus on the active object
        with bpy.context.temp_override(**view3d_context):
            bpy.ops.view3d.view_selected()
        
        return {'success': True, 'message': f'Focused on active object "{bpy.context.active_object.name}"'}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


def ensure_view3d_context():
    """Ensure VIEW_3D context is available for viewport operations"""
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for region in area.regions:
                if region.type == 'WINDOW':
                    return {'area': area, 'region': region}
    return None

def select_object(object_name: str, deselect_others: bool = True) -> dict:
    """
    AI tool: Select an object in the scene.
    
    Args:
        object_name: Name of the object to select
        deselect_others: Whether to deselect other objects first
        
    Returns:
        Dict with operation result
    """
    try:
        obj = bpy.data.objects.get(object_name)
        if obj is None:
            return {'success': False, 'error': f'Object "{object_name}" not found'}
        
        if obj.hide_viewport:
            return {'success': False, 'error': f'Object "{object_name}" is hidden'}
        
        if deselect_others:
            bpy.ops.object.select_all(action='DESELECT')
        
        obj.select_set(True)
        
        return {'success': True, 'message': f'Object "{object_name}" selected'}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


def set_active_object(object_name: str) -> dict:
    """
    AI tool: Make an object the active object in the scene.
    
    Args:
        object_name: Name of the object to make active
        
    Returns:
        Dict with operation result
    """
    try:
        # First select the object
        select_result = select_object(object_name)
        if not select_result['success']:
            return select_result  # Return the error from select_object
        
        # Get the object by name (we know it exists from select_object)
        obj = bpy.data.objects.get(object_name)
        
        # Make it active
        bpy.context.view_layer.objects.active = obj
        
        return {'success': True, 'message': f'Object "{object_name}" selected and set as active'}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


def handle_delete_object(object_name: str) -> dict:
    """
    AI tool: Delete an object from the scene.
    
    Args:
        object_name: Name of the object to delete
        
    Returns:
        Dict with operation result
    """
    try:
        # Find the object
        obj = bpy.data.objects.get(object_name)
        if not obj:
            return {
                "status": "error",
                "message": f"Object '{object_name}' not found",
                "error_code": "OBJECT_NOT_FOUND"
            }
        
        # Select only this object and make it active
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        
        # Delete the object
        bpy.ops.object.delete(use_global=False, confirm=False)
        
        return {
            "status": "success",
            "message": f"Deleted object '{object_name}'",
            "data": {"deleted_object": object_name}
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to delete object: {str(e)}",
            "error_code": "DELETE_ERROR"
        }
