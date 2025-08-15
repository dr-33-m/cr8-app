import bpy
import json
from bpy.props import StringProperty, EnumProperty, BoolProperty
from bpy.types import Operator
from mathutils import Vector
from ..utils import server_utils
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TEMPLATE_OT_SaveProductAnimation(Operator):
    """Save current empty's animation as a reusable template"""
    bl_idname = "template.save_product_animation"
    bl_label = "Save Product Animation"

    @classmethod
    def get_addon_preferences(cls, context):
        addon_name = __package__.split('.')[0]
        prefs = context.preferences.addons.get(addon_name)
        if prefs is None:
            raise RuntimeError(
                f"Could not find addon preferences for {addon_name}")
        return prefs.preferences

    def execute(self, context):
        props = context.scene.product_template_props
        selected_object = context.active_object

        if not selected_object:
            self.report({'ERROR'}, "No active object selected")
            return {'CANCELLED'}

        # Determine if we're dealing with an empty or a product
        if selected_object.type == 'EMPTY':
            # We selected an empty - check if it has children
            has_children = False
            product = None

            for obj in bpy.data.objects:
                if obj.parent == selected_object:
                    has_children = True
                    # Try to find a mesh child to use as the product reference
                    if hasattr(obj.data, 'vertices'):
                        product = obj
                        break

            if not has_children:
                self.report(
                    {'ERROR'}, "Selected empty has no children. Please select an empty that is parenting a product.")
                return {'CANCELLED'}

            # If we didn't find a mesh child, use the first child as product reference
            if not product:
                for obj in bpy.data.objects:
                    if obj.parent == selected_object:
                        product = obj
                        break

            parent_empty = selected_object

        else:
            # We selected a product - check if it has a parent empty
            if not selected_object.parent or selected_object.parent.type != 'EMPTY':
                self.report(
                    {'ERROR'}, "Selected object has no parent empty. Please select an empty or an object with a parent empty.")
                return {'CANCELLED'}

            product = selected_object
            parent_empty = product.parent

        # Verify the parent has animation data
        if not parent_empty.animation_data or not parent_empty.animation_data.action:
            self.report({'ERROR'}, "Parent empty has no animation data")
            return {'CANCELLED'}

        try:
            addon_prefs = self.get_addon_preferences(context)
            if not addon_prefs.user_id:
                self.report(
                    {'ERROR'}, "Please set your User ID in addon preferences")
                return {'CANCELLED'}

            # Get animation data from parent empty
            animation_data = self.extract_animation_data(parent_empty)

            if not animation_data:
                self.report(
                    {'ERROR'}, "No animation data found on parent empty")
                return {'CANCELLED'}

            # Add object type info
            animation_data['object_type'] = parent_empty.type

            # Save product information for reference if we have a product
            if product:
                animation_data['product_type'] = product.type

                # Add parent-child relationship information
                animation_data['parent_child_relationship'] = {
                    'parent_type': product.parent_type,
                    'parent_bone': product.parent_bone if product.parent_bone else ""
                }

                # Add pivot point and bounding box data for the product
                if hasattr(product.data, 'vertices'):
                    # For mesh objects, save bounding box info
                    bbox_center, bbox_dimensions = self.calculate_bounding_box(
                        product)
                    animation_data['product_bbox_center'] = bbox_center
                    animation_data['product_bbox_dimensions'] = bbox_dimensions

            # Structure the data according to the required format
            template_data = {
                'name': props.template_name,
                'type': 'product',
                'templateData': {
                    'category': props.animation_category,
                    'animation_data': animation_data,
                    'duration': context.scene.frame_end - context.scene.frame_start,
                    'base_rotation_mode': parent_empty.rotation_mode
                },
                'is_public': props.is_public
            }

            # Upload to server
            result = server_utils.upload_template(
                context, template_data, props.thumbnail_path)

            self.report(
                {'INFO'}, f"Empty animation '{props.template_name}' saved successfully")
            return {'FINISHED'}

        except Exception as e:
            logger.exception("Error saving animation")
            self.report({'ERROR'}, f"Error saving template: {str(e)}")
            return {'CANCELLED'}

    def calculate_bounding_box(self, obj):
        """Calculate object's bounding box in local space"""
        bbox_corners = [obj.matrix_world @
                        Vector(corner) for corner in obj.bound_box]

        # Calculate center and dimensions
        min_x = min(corner.x for corner in bbox_corners)
        min_y = min(corner.y for corner in bbox_corners)
        min_z = min(corner.z for corner in bbox_corners)
        max_x = max(corner.x for corner in bbox_corners)
        max_y = max(corner.y for corner in bbox_corners)
        max_z = max(corner.z for corner in bbox_corners)

        center = [(min_x + max_x)/2, (min_y + max_y)/2, (min_z + max_z)/2]
        dimensions = [max_x - min_x, max_y - min_y, max_z - min_z]

        return center, dimensions

    def extract_animation_data(self, obj):
        """Extract animation data in a format that can be reliably reapplied"""
        if not obj.animation_data or not obj.animation_data.action:
            return None

        action = obj.animation_data.action

        # Store the action name and general properties
        data = {
            'action_name': action.name,
            'frame_range': list(action.frame_range),
            'fcurves': []
        }

        # Extract all fcurves data
        for fc in action.fcurves:
            fcurve_data = {
                'data_path': fc.data_path,
                'array_index': fc.array_index,
                'extrapolation': fc.extrapolation,
                'keyframes': []
            }

            # Extract keyframe data
            for kp in fc.keyframe_points:
                keyframe = {
                    'co': list(kp.co),  # Frame, value
                    'interpolation': kp.interpolation,
                    'handle_left': list(kp.handle_left),
                    'handle_right': list(kp.handle_right),
                    'handle_left_type': kp.handle_left_type,
                    'handle_right_type': kp.handle_right_type,
                    'easing': kp.easing
                }
                fcurve_data['keyframes'].append(keyframe)

            data['fcurves'].append(fcurve_data)

        # Extract also drivers if present
        if obj.animation_data.drivers:
            data['drivers'] = []
            for driver in obj.animation_data.drivers:
                driver_data = {
                    'data_path': driver.data_path,
                    'array_index': driver.array_index,
                    'driver_type': driver.driver.type,
                    'expression': driver.driver.expression,
                    'variables': []
                }

                # Extract variables
                for var in driver.driver.variables:
                    var_data = {
                        'name': var.name,
                        'type': var.type,
                        'targets': []
                    }

                    # Extract targets
                    for i, target in enumerate(var.targets):
                        target_data = {
                            'id_type': target.id_type if target.id else '',
                            'data_path': target.data_path,
                            'transform_type': target.transform_type,
                            'transform_space': target.transform_space
                        }
                        var_data['targets'].append(target_data)

                    driver_data['variables'].append(var_data)

                data['drivers'].append(driver_data)

        return data


class TEMPLATE_OT_LoadProductAnimation(Operator):
    """Apply animation template to an empty"""
    bl_idname = "template.load_product_animation"
    bl_label = "Load Product Animation"

    template_name: StringProperty(
        name="Template Name",
        description="Name of the template to load"
    )
    template_id: StringProperty(
        name="Template ID",
        description="ID of the template to load"
    )
    template_data: StringProperty(
        name="Template Data",
        description="JSON string of template data"
    )

    # Add options for users to control the application
    adjust_to_object_size: BoolProperty(
        name="Adjust for Object Size",
        description="Scale animation to match target object size",
        default=True
    )

    preserve_original_timing: BoolProperty(
        name="Preserve Original Timing",
        description="Keep the original timing of keyframes",
        default=True
    )

    create_parent_empty: BoolProperty(
        name="Create Parent Empty",
        description="Create a parent empty if needed",
        default=True
    )

    preserve_target_position: BoolProperty(
        name="Preserve Target Position",
        description="Keep the target empty at its current position when applying animation",
        default=True
    )

    def execute(self, context):
        selected_object = context.active_object

        if not selected_object:
            self.report({'ERROR'}, "No active object selected")
            return {'CANCELLED'}

        # Determine if we're dealing with an empty or a product
        if selected_object.type == 'EMPTY':
            # We selected an empty - we'll apply animation to this
            parent_empty = selected_object

            # Check if the empty has any children to use for scaling reference
            product = None
            for obj in bpy.data.objects:
                if obj.parent == parent_empty and hasattr(obj.data, 'vertices'):
                    product = obj
                    break
        else:
            # We selected a product - check if it has a parent empty
            parent_empty = selected_object.parent
            product = selected_object

            if not parent_empty:
                if self.create_parent_empty:
                    # Create a new empty as parent
                    parent_empty = self.create_empty_parent(context, product)
                    self.report({'INFO'}, "Created new parent empty")
                else:
                    self.report(
                        {'ERROR'}, "Selected object has no parent empty. Enable 'Create Parent Empty' option or select an empty directly.")
                    return {'CANCELLED'}

        try:
            # Extract the animation data from the new structure
            template_data = json.loads(self.template_data)
            animation_data = template_data.get('animation_data', {})

            if not animation_data:
                self.report({'ERROR'}, "No animation data found in template")
                return {'CANCELLED'}

            # Check compatibility
            if 'object_type' in animation_data and animation_data['object_type'] != parent_empty.type:
                self.report(
                    {'WARNING'}, f"Template was created for a {animation_data['object_type']} object, but target is a {parent_empty.type} object. Results may vary.")

            # Set rotation mode if needed
            base_rotation_mode = template_data.get('base_rotation_mode', 'XYZ')
            if base_rotation_mode != parent_empty.rotation_mode:
                logger.info(
                    f"Setting rotation mode from {parent_empty.rotation_mode} to {base_rotation_mode}")
                parent_empty.rotation_mode = base_rotation_mode

            # Store original position before applying animation
            original_location = parent_empty.location.copy(
            ) if self.preserve_target_position else None

            # Apply the animation to the parent empty
            self.apply_animation(parent_empty, animation_data, product)

            # Adjust animation to preserve original position if requested
            if self.preserve_target_position and original_location is not None:
                self.adjust_animation_position(parent_empty, original_location)

            # Set scene end frame if needed
            duration = template_data.get('duration')
            if duration:
                context.scene.frame_end = max(
                    context.scene.frame_end,
                    context.scene.frame_start + duration
                )

            self.report(
                {'INFO'}, f"Animation '{self.template_name}' applied to empty successfully")
            return {'FINISHED'}

        except Exception as e:
            logger.exception("Error applying animation")
            self.report({'ERROR'}, f"Error applying animation: {str(e)}")
            return {'CANCELLED'}

    def create_empty_parent(self, context, product):
        """Create a new empty object and make it the parent of the product"""
        # Create a new empty
        empty = bpy.data.objects.new(f"{product.name}_Parent", None)
        empty.empty_display_type = 'ARROWS'  # You can choose different display types
        empty.empty_display_size = 1.0

        # Add to the scene
        context.collection.objects.link(empty)

        # Position the empty at the product's location
        empty.location = product.location.copy()

        # Make the product a child of the empty
        product.parent = empty
        product.matrix_parent_inverse = empty.matrix_world.inverted()

        # Reset product location since it's now relative to parent
        product.location = (0, 0, 0)

        return empty

    def adjust_animation_position(self, obj, original_location):
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

    def apply_animation(self, obj, animation_data, product=None):
        """Apply the template animation to the object"""
        # Make sure the object has animation data
        if not obj.animation_data:
            obj.animation_data_create()

        # Remove existing action if present
        if obj.animation_data.action:
            obj.animation_data.action = None

        # Create new action
        action_name = f"{obj.name}_{self.template_name}_action"
        action = bpy.data.actions.new(name=action_name)
        obj.animation_data.action = action

        # Calculate scale adjustments if needed
        scale_factor = 1.0
        if self.adjust_to_object_size and product and 'product_bbox_dimensions' in animation_data and hasattr(product.data, 'vertices'):
            # Get current object dimensions
            current_bbox, current_dims = self.calculate_bounding_box(product)
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
            # Create new fcurve
            data_path = fc_data['data_path']
            array_index = fc_data['array_index']

            # Skip certain data paths if we don't want to transfer everything
            if data_path.startswith('delta_'):  # Example of paths to skip
                continue

            fc = action.fcurves.new(data_path=data_path, index=array_index)
            fc.extrapolation = fc_data.get('extrapolation', 'CONSTANT')

            # Apply scaling for location/scale paths if needed
            apply_scale = False
            if self.adjust_to_object_size:
                if data_path == 'location':
                    apply_scale = True
                elif data_path == 'scale':
                    # For scale we might want special handling
                    pass

            # Add keyframes
            for kf_data in fc_data.get('keyframes', []):
                # Create a copy to avoid modifying the original
                co = list(kf_data['co'])

                # Apply scaling if needed
                if apply_scale and array_index < 3:  # Only scale XYZ
                    co[1] *= scale_factor

                kf = fc.keyframe_points.insert(co[0], co[1])

                # Set keyframe properties
                kf.interpolation = kf_data.get('interpolation', 'BEZIER')
                kf.handle_left_type = kf_data.get('handle_left_type', 'AUTO')
                kf.handle_right_type = kf_data.get('handle_right_type', 'AUTO')

                # Set handle positions
                if 'handle_left' in kf_data and 'handle_right' in kf_data:
                    # Scale handles if needed
                    hl = list(kf_data['handle_left'])  # Create a copy
                    hr = list(kf_data['handle_right'])  # Create a copy

                    if apply_scale and array_index < 3:
                        hl[1] *= scale_factor
                        hr[1] *= scale_factor

                    kf.handle_left = hl
                    kf.handle_right = hr

                kf.easing = kf_data.get('easing', 'AUTO')

        # Apply drivers if present
        if 'drivers' in animation_data:
            for driver_data in animation_data.get('drivers', []):
                # Add driver
                data_path = driver_data['data_path']
                array_index = driver_data['array_index']

                # Create driver
                try:
                    driver = obj.animation_data.drivers.new(
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

    def calculate_bounding_box(self, obj):
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
