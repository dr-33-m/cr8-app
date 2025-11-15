import bpy

def list_scene_objects() -> list:
    """
    AI tool: Get detailed list of all objects in the current scene.
    
    Returns:
        List of dictionaries with object name, type, and basic transform info
    """
    try:
        objects_info = []
        
        for obj in bpy.data.objects:
            obj_info = {
                'name': obj.name,
                'type': obj.type,
                'visible': obj.visible_get(),
                'selected': obj.select_get(),
                'active': obj == bpy.context.active_object,
                'location': list(obj.location),
                'rotation': list(obj.rotation_euler),
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
                    snap: bool = False, snap_target: str = 'CLOSEST') -> dict:
    """
    AI tool: Resize/scale selected objects.
    
    Args:
        value_x, value_y, value_z: Scale factors for each axis
        constraint_x, constraint_y, constraint_z: Lock transformation to specific axes
        snap: Enable snapping
        snap_target: Snap target ('CLOSEST', 'CENTER', 'MEDIAN', 'ACTIVE')
    
    Returns:
        Dict with operation result
    """
    try:
        bpy.ops.transform.resize(
            value=(value_x, value_y, value_z),
            constraint_axis=(constraint_x, constraint_y, constraint_z),
            snap=snap,
            snap_target=snap_target
        )
        return {'success': True, 'message': f'Scaled objects by ({value_x}, {value_y}, {value_z})'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def transform_translate(value_x: float = 0.0, value_y: float = 0.0, value_z: float = 0.0,
                       constraint_x: bool = False, constraint_y: bool = False, constraint_z: bool = False,
                       snap: bool = False, snap_target: str = 'CLOSEST') -> dict:
    """
    AI tool: Translate/move selected objects to absolute positions.
    
    Args:
        value_x, value_y, value_z: Absolute position coordinates
        constraint_x, constraint_y, constraint_z: Lock transformation to specific axes
        snap: Enable snapping
        snap_target: Snap target ('CLOSEST', 'CENTER', 'MEDIAN', 'ACTIVE')
    
    Returns:
        Dict with operation result
    """
    try:
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
                    snap: bool = False, snap_target: str = 'CLOSEST') -> dict:
    """
    AI tool: Rotate selected objects to absolute rotation on all axes.
    
    Args:
        value_x, value_y, value_z: Absolute rotation values in radians for each axis
        constraint_x, constraint_y, constraint_z: Lock transformation to specific axes
        snap: Enable snapping
        snap_target: Snap target ('CLOSEST', 'CENTER', 'MEDIAN', 'ACTIVE')
    
    Returns:
        Dict with operation result
    """
    try:
        if bpy.context.active_object:
            obj = bpy.context.active_object
            
            # Set the rotation directly
            obj.rotation_euler.x = value_x
            obj.rotation_euler.y = value_y
            obj.rotation_euler.z = value_z
            
            # Update the object to reflect changes
            obj.update_tag(refresh={'OBJECT'})
            bpy.context.view_layer.update()
            
            return {'success': True, 'message': f'Set object rotation to ({value_x}, {value_y}, {value_z}) radians'}
        else:
            return {'success': False, 'error': 'No active object'}
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
