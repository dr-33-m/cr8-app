import bpy
from mathutils import Vector, Matrix


def get_relative_transform(obj, target):
    """Calculate relative transform between object and target"""
    target_inv = target.matrix_world.inverted()
    return target_inv @ obj.matrix_world


def get_relative_location(location, target_matrix):
    """Convert world location to target-relative location"""
    target_inv = target_matrix.inverted()
    relative_loc = target_inv @ Vector(location)
    return list(relative_loc)


def relative_to_world_location(relative_loc, target_matrix):
    """Convert target-relative location to world location"""
    return target_matrix @ Vector(relative_loc)


def ensure_fcurve(action, data_path, array_index):
    """Get existing F-curve or create new one if it doesn't exist"""
    for fc in action.fcurves:
        if fc.data_path == data_path and fc.array_index == array_index:
            fc.keyframe_points.clear()
            return fc
    return action.fcurves.new(data_path=data_path, index=array_index)


def apply_animation_data(obj, action, animation_data, target_empty):
    """Apply animation data to an object (light or camera)"""
    if not animation_data or not animation_data.get('keyframes'):
        return False

    # Ensure object has animation data
    if not obj.animation_data:
        obj.animation_data_create()
    obj.animation_data.action = action

    # Process keyframes
    for kf_data in animation_data['keyframes']:
        if kf_data['property'] == 'location':
            # Handle location keyframes
            world_loc = relative_to_world_location(
                kf_data['value'],
                target_empty.matrix_world
            )

            # Create location fcurves if they don't exist
            for i in range(3):
                fcurve = ensure_fcurve(action, "location", i)
                point = fcurve.keyframe_points.insert(
                    kf_data['frame'],
                    world_loc[i]
                )
                point.interpolation = 'LINEAR'

        elif kf_data.get('property') == 'light_property':
            # Handle light-specific properties
            fcurve = ensure_fcurve(
                action,
                kf_data['path'],
                kf_data['array_index']
            )
            point = fcurve.keyframe_points.insert(
                kf_data['frame'],
                kf_data['value']
            )
            if 'handle_left' in kf_data and 'handle_right' in kf_data:
                point.handle_left = kf_data['handle_left']
                point.handle_right = kf_data['handle_right']
            point.interpolation = kf_data.get('interpolation', 'BEZIER')

        else:
            # Handle other properties (rotation, etc.)
            fcurve = ensure_fcurve(
                action,
                kf_data.get('path', f"{kf_data['property']}"),
                kf_data.get('array_index', 0)
            )
            point = fcurve.keyframe_points.insert(
                kf_data['frame'],
                kf_data['value']
            )
            if 'handle_left' in kf_data and 'handle_right' in kf_data:
                point.handle_left = kf_data['handle_left']
                point.handle_right = kf_data['handle_right']
            point.interpolation = kf_data.get('interpolation', 'BEZIER')

    # Update fcurves
    for fc in action.fcurves:
        fc.update()

    return True


def get_animatable_light_properties(light):
    """Get a list of animatable properties for a light"""
    properties = {
        'energy': 'data.energy',
        'color': 'data.color',
        'shadow_soft_size': 'data.shadow_soft_size',
    }

    # Add type-specific properties
    if light.data.type == 'SPOT':
        properties.update({
            'spot_size': 'data.spot_size',
            'spot_blend': 'data.spot_blend',
        })
    elif light.data.type == 'AREA':
        properties.update({
            'size': 'data.size',
            'size_y': 'data.size_y',
        })

    return properties
