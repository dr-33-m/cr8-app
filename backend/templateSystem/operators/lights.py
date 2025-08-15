from ..utils import animation_utils, server_utils
from bpy.types import Operator
from mathutils import Matrix, Vector
from bpy.props import StringProperty
import json
import bpy


class TEMPLATE_OT_SaveLightSetup(Operator):
    """Save current light setup as a template to server"""
    bl_idname = "template.save_light_setup"
    bl_label = "Save Light Setup"

    @classmethod
    def get_addon_preferences(cls, context):
        """Get addon preferences safely"""
        addon_name = __package__.split(
            '.')[0]  # Gets the root addon package name
        prefs = context.preferences.addons.get(addon_name)
        if prefs is None:
            raise RuntimeError(
                f"Could not find addon preferences for {addon_name}")
        return prefs.preferences

    def get_light_data(self, light_obj):
        """Extract light data and settings"""
        light_data = light_obj.data
        data = {
            'name': light_obj.name,
            'type': light_data.type,
            'energy': light_data.energy,
            'color': list(light_data.color),
            'shadow_soft_size': light_data.shadow_soft_size,
            'use_shadow': light_data.use_shadow,
        }

        # Add type-specific properties
        if light_data.type == 'SPOT':
            data.update({
                'spot_size': light_data.spot_size,
                'spot_blend': light_data.spot_blend
            })
        elif light_data.type == 'AREA':
            data.update({
                'size': light_data.size,
                'size_y': light_data.size_y,
                'shape': light_data.shape
            })

        return data

    def execute(self, context):
        props = context.scene.light_template_props

        if not props.target_empty:
            self.report({'ERROR'}, "Target empty must be selected")
            return {'CANCELLED'}

        try:
            addon_prefs = self.get_addon_preferences(context)
            if not addon_prefs.user_id:
                self.report(
                    {'ERROR'}, "Please set your User ID in the addon preferences")
                return {'CANCELLED'}

            # Collect all selected lights
            selected_lights = [
                obj for obj in bpy.context.selected_objects if obj.type == 'LIGHT']
            if not selected_lights:
                self.report({'ERROR'}, "No lights selected")
                return {'CANCELLED'}

            lights_data = []
            for light_obj in selected_lights:
                light_data = {
                    'light_settings': self.get_light_data(light_obj),
                    'relative_transform': [list(row) for row in animation_utils.get_relative_transform(light_obj, props.target_empty)],
                    'animation_data': animation_utils.get_light_animation_data(light_obj, props.target_empty),
                    'constraints': []
                }

                # Save constraints
                for constraint in light_obj.constraints:
                    if constraint.type in {'TRACK_TO', 'COPY_LOCATION', 'COPY_ROTATION'}:
                        constraint_data = {
                            'type': constraint.type,
                            'target': props.target_empty.name if constraint.target == props.target_empty else None
                        }
                        if constraint.type == 'TRACK_TO':
                            constraint_data.update({
                                'track_axis': constraint.track_axis,
                                'up_axis': constraint.up_axis,
                            })
                        light_data['constraints'].append(constraint_data)

                lights_data.append(light_data)

            template_data = {
                'name': props.template_name,
                'type': 'light',
                'lights': lights_data,
                'is_public': props.is_public
            }

            result = server_utils.upload_template(
                context, template_data, props.thumbnail_path)
            self.report(
                {'INFO'}, f"Light setup '{props.template_name}' uploaded successfully")
            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Error saving template: {str(e)}")
            return {'CANCELLED'}


class TEMPLATE_OT_LoadLightSetup(Operator):
    """Load and apply a light setup template from the server"""
    bl_idname = "template.load_light_setup"
    bl_label = "Load Light Setup"

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

    def create_light(self, light_data, target_empty):
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

    def execute(self, context):
        props = context.scene.light_template_props

        if not props.target_empty:
            self.report({'ERROR'}, "Target empty must be selected")
            return {'CANCELLED'}

        try:
            template_data = json.loads(self.template_data)

            created_lights = []
            for light_data in template_data['lights']:
                # Create the light
                light_obj = self.create_light(light_data, props.target_empty)
                created_lights.append(light_obj)

                # Apply constraints
                for constraint_data in light_data['constraints']:
                    constraint = light_obj.constraints.new(
                        constraint_data['type'])
                    constraint.target = props.target_empty

                    if constraint_data['type'] == 'TRACK_TO':
                        constraint.track_axis = constraint_data['track_axis']
                        constraint.up_axis = constraint_data['up_axis']

                # Apply animation data
                if light_data.get('animation_data'):
                    action_name = f"{light_obj.name}_action"
                    action = bpy.data.actions.new(name=action_name)

                    # Create and apply animation data similar to camera template
                    animation_utils.apply_animation_data(
                        light_obj,
                        action,
                        light_data['animation_data'],
                        props.target_empty
                    )

            self.report(
                {'INFO'}, f"Light setup '{self.template_name}' applied successfully")
            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Error loading template: {str(e)}")
            return {'CANCELLED'}
