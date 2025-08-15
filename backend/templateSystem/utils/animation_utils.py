from mathutils import Vector, Matrix
import bpy


def get_relative_transform(camera, target):
    """Calculate relative transform between camera and target"""
    target_inv = target.matrix_world.inverted()
    return target_inv @ camera.matrix_world


def get_relative_location(location, target_matrix):
    """Convert world location to target-relative location"""
    target_inv = target_matrix.inverted()
    relative_loc = target_inv @ Vector(location)
    return list(relative_loc)


def world_to_relative_keyframes(fcurves, target_empty):
    """Convert world-space keyframes to target-relative space"""
    relative_data = []

    # Group fcurves by property (location, rotation, etc.)
    property_groups = {}
    for fcurve in fcurves:
        prop_path = fcurve.data_path
        if prop_path not in property_groups:
            property_groups[prop_path] = []
        property_groups[prop_path].append(fcurve)

    # Process each frame
    for prop_path, curves in property_groups.items():
        # Handle location keyframes specially
        if prop_path.endswith('location'):
            # Get all unique frame numbers
            frames = set()
            for fc in curves:
                frames.update(kf.co[0] for kf in fc.keyframe_points)

            # Process each frame
            for frame in sorted(frames):
                # Get the world location at this frame
                world_loc = [
                    curves[i].evaluate(frame) if i < len(curves) else 0
                    for i in range(3)
                ]

                # Get target's transform at this frame
                target_empty.keyframe_insert(data_path="location", frame=frame)
                target_matrix = target_empty.matrix_world.copy()

                # Convert to relative location
                relative_loc = get_relative_location(world_loc, target_matrix)

                relative_data.append({
                    'frame': frame,
                    'property': 'location',
                    'value': relative_loc
                })

        # Handle light-specific properties (energy, color, etc.)
        elif prop_path.startswith('data.'):
            prop_name = prop_path.split('.')[-1]

            for fc in curves:
                for kf in fc.keyframe_points:
                    relative_data.append({
                        'frame': kf.co[0],
                        'property': 'light_property',
                        'path': prop_path,
                        'property_name': prop_name,
                        'array_index': fc.array_index,
                        'value': kf.co[1],
                        'handle_left': tuple(kf.handle_left),
                        'handle_right': tuple(kf.handle_right),
                        'interpolation': kf.interpolation
                    })

        # Handle other properties (rotation, etc.)
        else:
            for fc in curves:
                for kf in fc.keyframe_points:
                    relative_data.append({
                        'frame': kf.co[0],
                        'property': prop_path.split('.')[-1],
                        'path': fc.data_path,
                        'array_index': fc.array_index,
                        'value': kf.co[1],
                        'handle_left': tuple(kf.handle_left),
                        'handle_right': tuple(kf.handle_right),
                        'interpolation': kf.interpolation
                    })

    return relative_data


def get_camera_animation_data(camera, target_empty):
    """Extract all animation data from the camera in target-relative space"""
    if not camera.animation_data or not camera.animation_data.action:
        return None

    return {
        'action_name': camera.animation_data.action.name,
        'keyframes': world_to_relative_keyframes(
            camera.animation_data.action.fcurves,
            target_empty
        )
    }


def relative_to_world_location(relative_loc, target_matrix):
    """Convert target-relative location to world location"""
    return target_matrix @ Vector(relative_loc)


def get_light_animation_data(light_obj, target_empty):
    """Extract all animation data from the light in target-relative space"""
    if not light_obj.animation_data or not light_obj.animation_data.action:
        return None

    return {
        'action_name': light_obj.animation_data.action.name,
        'keyframes': world_to_relative_keyframes(
            light_obj.animation_data.action.fcurves,
            target_empty
        )
    }


def apply_animation_data(obj, action, animation_data, target_empty):
    """Apply animation data to an object (light or camera)"""
    if not animation_data:
        return

    # Create a new action if none exists
    if not action:
        action = bpy.data.actions.new(name=f"{obj.name}_action")

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

        elif kf_data['property'] == 'rotation':
            # Handle rotation keyframes
            fcurve = ensure_fcurve(
                action,
                kf_data['path'],
                kf_data['array_index']
            )
            point = fcurve.keyframe_points.insert(
                kf_data['frame'],
                kf_data['value']
            )
            point.handle_left = kf_data['handle_left']
            point.handle_right = kf_data['handle_right']
            point.interpolation = kf_data['interpolation']

        elif kf_data['property'] == 'light_property':
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
            point.handle_left = kf_data['handle_left']
            point.handle_right = kf_data['handle_right']
            point.interpolation = kf_data['interpolation']


def ensure_fcurve(action, data_path, array_index):
    """Get existing F-curve or create new one if it doesn't exist"""
    for fc in action.fcurves:
        if fc.data_path == data_path and fc.array_index == array_index:
            fc.keyframe_points.clear()
            return fc
    return action.fcurves.new(data_path=data_path, index=array_index)


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
