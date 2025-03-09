"""
Animation command handlers for WebSocket communication.
"""

import logging
import bpy
from mathutils import Matrix, Vector
from ...core.animation_utils import apply_animation_data, ensure_fcurve, relative_to_world_location
from ..utils.response_manager import ResponseManager

# Configure logging
logger = logging.getLogger(__name__)


class AnimationHandlers:
    """Handlers for animation-related WebSocket commands."""

    # Get a single shared instance of ResponseManager
    response_manager = ResponseManager.get_instance()

    @staticmethod
    def handle_load_camera_animation(data):
        """Handle loading camera animation to an empty"""
        try:
            message_id = data.get('message_id')
            logger.info(
                f"Handling load camera animation request with message_id: {message_id}")

            # Extract parameters from the request
            template_data = data.get('template_data', {})
            empty_name = data.get('empty_name')

            if not empty_name:
                raise ValueError("No target empty specified")

            # Find the target empty in the scene
            target_empty = bpy.data.objects.get(empty_name)
            if not target_empty:
                raise ValueError(
                    f"Target empty '{empty_name}' not found in scene")

            # Apply the camera animation
            result = AnimationHandlers.apply_camera_animation(
                template_data, target_empty)

            # Send response
            AnimationHandlers.response_manager.send_response('camera_animation_result', result.get('success', False), {
                "data": result,
                "message_id": message_id
            })

        except Exception as e:
            logger.error(f"Error loading camera animation: {e}")
            import traceback
            traceback.print_exc()

            # Send error response
            AnimationHandlers.response_manager.send_response('camera_animation_result', False, {
                "message": str(e),
                "message_id": data.get('message_id')
            })

    @staticmethod
    def handle_load_light_animation(data):
        """Handle loading light animation to an empty"""
        try:
            message_id = data.get('message_id')
            logger.info(
                f"Handling load light animation request with message_id: {message_id}")

            # Extract parameters from the request
            template_data = data.get('template_data', {})
            empty_name = data.get('empty_name')

            if not empty_name:
                raise ValueError("No target empty specified")

            # Find the target empty in the scene
            target_empty = bpy.data.objects.get(empty_name)
            if not target_empty:
                raise ValueError(
                    f"Target empty '{empty_name}' not found in scene")

            # Apply the light animation
            result = AnimationHandlers.apply_light_animation(
                template_data, target_empty)

            # Send response
            AnimationHandlers.response_manager.send_response('light_animation_result', result.get('success', False), {
                "data": result,
                "message_id": message_id
            })

        except Exception as e:
            logger.error(f"Error loading light animation: {e}")
            import traceback
            traceback.print_exc()

            # Send error response
            AnimationHandlers.response_manager.send_response('light_animation_result', False, {
                "message": str(e),
                "message_id": data.get('message_id')
            })

    @staticmethod
    def handle_load_product_animation(data):
        """Handle loading product animation to an empty"""
        try:
            message_id = data.get('message_id')
            logger.info(
                f"Handling load product animation request with message_id: {message_id}")

            # Extract parameters from the request
            template_data = data.get('template_data', {})
            empty_name = data.get('empty_name')

            if not empty_name:
                raise ValueError("No target empty specified")

            # Find the target empty in the scene
            target_empty = bpy.data.objects.get(empty_name)
            if not target_empty:
                raise ValueError(
                    f"Target empty '{empty_name}' not found in scene")

            # Apply the product animation
            result = AnimationHandlers.apply_product_animation(
                template_data, target_empty)

            # Send response
            AnimationHandlers.response_manager.send_response('product_animation_result', result.get('success', False), {
                "data": result,
                "message_id": message_id
            })

        except Exception as e:
            logger.error(f"Error loading product animation: {e}")
            import traceback
            traceback.print_exc()

            # Send error response
            AnimationHandlers.response_manager.send_response('product_animation_result', False, {
                "message": str(e),
                "message_id": data.get('message_id')
            })

    @staticmethod
    def create_or_get_fcurve(action, data_path, index):
        """Get existing F-curve or create new one if it doesn't exist"""
        for fc in action.fcurves:
            if fc.data_path == data_path and fc.array_index == index:
                fc.keyframe_points.clear()
                return fc
        return action.fcurves.new(data_path=data_path, index=index)

    @staticmethod
    def create_light(light_data, target_empty):
        """Create a new light with the specified settings"""
        # Create new light data and object
        light_settings = light_data['light_settings']
        light_data_block = bpy.data.lights.new(
            name=light_settings['name'], type=light_settings['type'])
        light_obj = bpy.data.objects.new(
            name=light_settings['name'], object_data=light_data_block)

        # Link to scene
        bpy.context.scene.collection.objects.link(light_obj)

        # Apply basic settings
        light_data_block.energy = light_settings['energy']
        light_data_block.color = light_settings['color']
        light_data_block.shadow_soft_size = light_settings['shadow_soft_size']
        light_data_block.use_shadow = light_settings['use_shadow']

        # Apply type-specific settings
        if light_settings['type'] == 'SPOT':
            light_data_block.spot_size = light_settings['spot_size']
            light_data_block.spot_blend = light_settings['spot_blend']
        elif light_settings['type'] == 'AREA':
            light_data_block.size = light_settings['size']
            light_data_block.size_y = light_settings['size_y']
            light_data_block.shape = light_settings['shape']

        # Apply transform
        relative_matrix = Matrix([Vector(row)
                                  for row in light_data['relative_transform']])
        light_obj.matrix_world = target_empty.matrix_world @ relative_matrix

        return light_obj

    @staticmethod
    def apply_camera_animation(template_data, target_empty):
        """Apply camera animation using the target empty"""
        try:
            template_name = template_data.get('name', 'camera')

            # Create new camera
            cam_data = bpy.data.cameras.new(
                name=f"{template_name}_camera")
            cam_obj = bpy.data.objects.new(
                f"{template_name}_camera", cam_data)
            bpy.context.scene.collection.objects.link(cam_obj)

            # Set as active camera
            bpy.context.scene.camera = cam_obj

            # Apply relative transform if available
            if 'relative_transform' in template_data:
                relative_matrix = Matrix(
                    [Vector(row) for row in template_data['relative_transform']])
                cam_obj.matrix_world = target_empty.matrix_world @ relative_matrix

            # Apply camera settings
            if 'focal_length' in template_data:
                cam_data.lens = template_data['focal_length']
            if 'dof_distance' in template_data:
                cam_data.dof.focus_distance = template_data['dof_distance']

            # Apply constraints
            for constraint_data in template_data.get('constraints', []):
                if constraint_data.get('type') == 'TRACK_TO':
                    constraint = cam_obj.constraints.new('TRACK_TO')
                    constraint.target = target_empty
                    constraint.track_axis = constraint_data.get(
                        'track_axis', 'TRACK_NEGATIVE_Z')
                    constraint.up_axis = constraint_data.get('up_axis', 'UP_Y')

            # Apply animation data
            if 'animation_data' in template_data:
                action_name = f"{template_name}_action"
                action = bpy.data.actions.new(name=action_name)

                # Create location fcurves
                loc_fcurves = [
                    AnimationHandlers.create_or_get_fcurve(
                        action, "location", i)
                    for i in range(3)
                ]

                # Apply keyframes
                for kf_data in template_data['animation_data']['keyframes']:
                    frame = kf_data['frame']

                    if kf_data['property'] == 'location':
                        target_matrix = target_empty.matrix_world.copy()
                        world_loc = relative_to_world_location(
                            kf_data['value'], target_matrix)

                        for i, value in enumerate(world_loc):
                            point = loc_fcurves[i].keyframe_points.insert(
                                frame, value)
                            point.interpolation = 'BEZIER'
                    else:
                        fcurve = AnimationHandlers.create_or_get_fcurve(
                            action,
                            kf_data['path'],
                            kf_data['array_index']
                        )
                        point = fcurve.keyframe_points.insert(
                            frame, kf_data['value'])
                        point.handle_left = kf_data['handle_left']
                        point.handle_right = kf_data['handle_right']
                        point.interpolation = kf_data['interpolation']

                if not cam_obj.animation_data:
                    cam_obj.animation_data_create()
                cam_obj.animation_data.action = action

            return {"success": True, "message": "Camera animation applied successfully"}
        except Exception as e:
            logger.error(f"Error applying camera animation: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": str(e)}

    @staticmethod
    def apply_light_animation(template_data, target_empty):
        """Apply light animation using the target empty"""
        try:
            created_lights = []

            # Process each light in the template
            for light_data in template_data.get('lights', []):
                # Create the light
                light_obj = AnimationHandlers.create_light(
                    light_data, target_empty)
                created_lights.append(light_obj)

                # Apply constraints
                for constraint_data in light_data.get('constraints', []):
                    constraint_type = constraint_data.get('type')
                    if constraint_type:
                        constraint = light_obj.constraints.new(constraint_type)
                        constraint.target = target_empty

                        if constraint_type == 'TRACK_TO':
                            constraint.track_axis = constraint_data.get(
                                'track_axis', 'TRACK_NEGATIVE_Z')
                            constraint.up_axis = constraint_data.get(
                                'up_axis', 'UP_Y')

                # Apply animation data
                if light_data.get('animation_data'):
                    action_name = f"{light_obj.name}_action"
                    action = bpy.data.actions.new(name=action_name)

                    # Apply animation keyframes using the utility function
                    apply_animation_data(
                        light_obj,
                        action,
                        light_data['animation_data'],
                        target_empty
                    )

            return {
                "success": True,
                "message": f"Light animation applied successfully with {len(created_lights)} lights",
                "lights_created": len(created_lights)
            }
        except Exception as e:
            logger.error(f"Error applying light animation: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": str(e)}

    @staticmethod
    def calculate_bounding_box(obj):
        """Calculate object's bounding box in local space"""
        # Ensure mesh is up to date
        depsgraph = bpy.context.evaluated_depsgraph_get()
        obj_eval = obj.evaluated_get(depsgraph)

        if not hasattr(obj_eval, 'bound_box'):
            return [0, 0, 0], [1, 1, 1]

        # Calculate center and dimensions
        bbox_corners = [obj_eval.matrix_world @
                        Vector(corner) for corner in obj_eval.bound_box]

        min_x = min(corner.x for corner in bbox_corners)
        min_y = min(corner.y for corner in bbox_corners)
        min_z = min(corner.z for corner in bbox_corners)
        max_x = max(corner.x for corner in bbox_corners)
        max_y = max(corner.y for corner in bbox_corners)
        max_z = max(corner.z for corner in bbox_corners)

        center = [(min_x + max_x)/2, (min_y + max_y)/2, (min_z + max_z)/2]
        dimensions = [max_x - min_x, max_y - min_y, max_z - min_z]

        return center, dimensions

    @staticmethod
    def adjust_animation_position(obj, original_location):
        """Adjust the animation to maintain the object's original position"""
        if not obj.animation_data or not obj.animation_data.action:
            return

        action = obj.animation_data.action

        # Find location fcurves
        loc_fcurves = [
            fc for fc in action.fcurves if fc.data_path == 'location']

        if not loc_fcurves or len(loc_fcurves) < 3:
            # If no location fcurves, create them
            for i in range(3):
                if i >= len(loc_fcurves):
                    action.fcurves.new(data_path='location', index=i)

        # Calculate the offset between current first keyframe and original location
        first_frame_loc = Vector([0, 0, 0])
        for i, fc in enumerate([fc for fc in action.fcurves if fc.data_path == 'location']):
            if fc.keyframe_points:
                # Get the value at the first keyframe
                first_frame_loc[i] = fc.keyframe_points[0].co[1]

        # Calculate offset
        offset = Vector(original_location) - first_frame_loc

        # Apply the offset to all location keyframes
        for i, fc in enumerate([fc for fc in action.fcurves if fc.data_path == 'location']):
            if i < 3:  # Only X, Y, Z
                for kp in fc.keyframe_points:
                    kp.co[1] += offset[i]
                    # Update handles
                    if hasattr(kp, 'handle_left') and hasattr(kp, 'handle_right'):
                        kp.handle_left[1] += offset[i]
                        kp.handle_right[1] += offset[i]

            # Update fcurve
            fc.update()

    @staticmethod
    def apply_product_animation(template_data, target_empty):
        """Apply product animation to the target empty (parent of a product)"""
        try:
            # Extract animation data
            animation_data = template_data.get('animation_data', {})
            if not animation_data:
                raise ValueError("No animation data found in template")

            # Log information about the target empty
            logger.info(
                f"Applying product animation to empty: {target_empty.name}")

            # Check if the empty has children (products)
            children = [child for child in target_empty.children]
            product = None
            if children:
                logger.info(
                    f"Found {len(children)} children objects for {target_empty.name}")
                # Find first child with vertices to use as product reference
                for child in children:
                    if hasattr(child.data, 'vertices'):
                        product = child
                        break
            else:
                logger.warning(
                    f"No children found for empty {target_empty.name}. Animation will only affect the empty.")

            # Set rotation mode if needed
            base_rotation_mode = template_data.get('base_rotation_mode', 'XYZ')
            if base_rotation_mode != target_empty.rotation_mode:
                logger.info(
                    f"Setting rotation mode from {target_empty.rotation_mode} to {base_rotation_mode}")
                target_empty.rotation_mode = base_rotation_mode

            # Store original position for position preservation
            original_location = target_empty.location.copy()

            # Create new action
            action_name = f"{target_empty.name}_{template_data.get('name', 'product')}_action"
            action = bpy.data.actions.new(name=action_name)

            # Ensure target has animation data
            if not target_empty.animation_data:
                target_empty.animation_data_create()
            target_empty.animation_data.action = action

            # Calculate scale adjustments if needed
            scale_factor = 1.0
            adjust_to_object_size = template_data.get(
                'adjust_to_object_size', True)

            if adjust_to_object_size and product and 'product_bbox_dimensions' in animation_data:
                # Get current object dimensions
                current_bbox, current_dims = AnimationHandlers.calculate_bounding_box(
                    product)
                template_dims = animation_data['product_bbox_dimensions']

                # Calculate average scale difference
                template_size = sum(template_dims) / 3.0
                current_size = sum(current_dims) / 3.0

                if template_size > 0:
                    scale_factor = current_size / template_size
                    logger.info(
                        f"Adjusting animation scale by factor: {scale_factor}")

            # Apply fcurves
            for fc_data in animation_data.get('fcurves', []):
                data_path = fc_data.get('data_path')
                array_index = fc_data.get('array_index', 0)

                # Skip certain data paths if we don't want to transfer everything
                if data_path and data_path.startswith('delta_'):
                    continue

                # Create fcurve
                fcurve = ensure_fcurve(action, data_path, array_index)
                fcurve.extrapolation = fc_data.get('extrapolation', 'CONSTANT')

                # Determine if we should apply scaling for this path
                apply_scale = False
                if adjust_to_object_size:
                    if data_path == 'location':
                        apply_scale = True

                # Add keyframes
                for kf_data in fc_data.get('keyframes', []):
                    # Create a copy to avoid modifying the original
                    co = list(kf_data.get('co', [0, 0]))

                    # Apply scaling if needed
                    if apply_scale and array_index < 3:  # Only scale XYZ
                        co[1] *= scale_factor

                    kf = fcurve.keyframe_points.insert(co[0], co[1])

                    # Set keyframe properties
                    kf.interpolation = kf_data.get('interpolation', 'BEZIER')

                    # Set handle types
                    if 'handle_left_type' in kf_data:
                        kf.handle_left_type = kf_data['handle_left_type']
                    if 'handle_right_type' in kf_data:
                        kf.handle_right_type = kf_data['handle_right_type']

                    # Set handle positions
                    if 'handle_left' in kf_data and 'handle_right' in kf_data:
                        # Scale handles if needed
                        hl = list(kf_data['handle_left'])
                        hr = list(kf_data['handle_right'])

                        if apply_scale and array_index < 3:
                            hl[1] *= scale_factor
                            hr[1] *= scale_factor

                        kf.handle_left = hl
                        kf.handle_right = hr

                    if 'easing' in kf_data:
                        kf.easing = kf_data['easing']

            # Apply drivers if present
            if 'drivers' in animation_data:
                for driver_data in animation_data.get('drivers', []):
                    # Add driver
                    data_path = driver_data['data_path']
                    array_index = driver_data['array_index']

                    # Create driver
                    try:
                        driver = target_empty.animation_data.drivers.new(
                            data_path, array_index)
                        driver.driver.type = driver_data.get(
                            'driver_type', 'AVERAGE')
                        driver.driver.expression = driver_data.get(
                            'expression', '')

                        # Add variables
                        for var_data in driver_data.get('variables', []):
                            var = driver.driver.variables.new()
                            var.name = var_data['name']
                            var.type = var_data['type']

                            # Add targets
                            for i, target_data in enumerate(var_data.get('targets', [])):
                                if i < len(var.targets):
                                    target = var.targets[i]
                                    target.data_path = target_data.get(
                                        'data_path', '')
                                    target.transform_type = target_data.get(
                                        'transform_type', 'LOC_X')
                                    target.transform_space = target_data.get(
                                        'transform_space', 'WORLD_SPACE')

                    except Exception as e:
                        logger.warning(
                            f"Could not add driver for {data_path}: {str(e)}")

            # Update fcurves
            for fc in action.fcurves:
                fc.update()

            # Adjust animation to preserve original position if requested
            preserve_target_position = template_data.get(
                'preserve_target_position', True)
            if preserve_target_position:
                AnimationHandlers.adjust_animation_position(
                    target_empty, original_location)

            # Set scene end frame if needed
            duration = template_data.get('duration')
            if duration:
                bpy.context.scene.frame_end = max(
                    bpy.context.scene.frame_end,
                    bpy.context.scene.frame_start + duration
                )

            return {
                "success": True,
                "message": "Product animation applied successfully to empty and its children",
                "empty_name": target_empty.name,
                "children_count": len(children)
            }
        except Exception as e:
            logger.error(f"Error applying product animation: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": str(e)}
