import bpy
import json
import os
from mathutils import Matrix, Vector
from bpy.props import StringProperty
from bpy.types import Operator
from ..utils import path_utils, animation_utils, server_utils


class TEMPLATE_OT_SaveCamera(Operator):
    """Save current camera setup as a template to server"""
    bl_idname = "template.save_camera"
    bl_label = "Save Camera Template"

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

    def execute(self, context):
        props = context.scene.camera_template_props
        camera = context.scene.camera

        if not camera or not props.target_empty:
            self.report(
                {'ERROR'}, "Both camera and target empty must be selected")
            return {'CANCELLED'}

        try:
            addon_prefs = self.get_addon_preferences(context)
            if not addon_prefs.user_id:
                self.report(
                    {'ERROR'}, "Please set your User ID in the addon preferences")
                return {'CANCELLED'}

            template_data = {
                'name': props.template_name,
                'type': 'camera',
                'relative_transform': [list(row) for row in animation_utils.get_relative_transform(camera, props.target_empty)],
                'focal_length': camera.data.lens,
                'dof_distance': camera.data.dof.focus_distance,
                'animation_data': animation_utils.get_camera_animation_data(camera, props.target_empty),
                'constraints': [],
                'is_public': props.is_public
            }

            # Save constraints
            for constraint in camera.constraints:
                if constraint.type == 'TRACK_TO':
                    constraint_data = {
                        'type': 'TRACK_TO',
                        'track_axis': constraint.track_axis,
                        'up_axis': constraint.up_axis,
                    }
                    template_data['constraints'].append(constraint_data)

            result = server_utils.upload_template(
                context, template_data, props.thumbnail_path)
            self.report(
                {'INFO'}, f"Camera template '{props.template_name}' uploaded successfully")
            return {'FINISHED'}

        except RuntimeError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error saving template: {str(e)}")
            return {'CANCELLED'}


class TEMPLATE_OT_LoadServerCamera(Operator):
    """Load and apply a camera template from the server"""
    bl_idname = "template.load_server_camera"
    bl_label = "Load Server Template"

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

    def create_or_get_fcurve(self, action, data_path, index):
        """Get existing F-curve or create new one if it doesn't exist"""
        for fc in action.fcurves:
            if fc.data_path == data_path and fc.array_index == index:
                fc.keyframe_points.clear()
                return fc
        return action.fcurves.new(data_path=data_path, index=index)

    def execute(self, context):
        props = context.scene.camera_template_props

        if not props.target_empty:
            self.report({'ERROR'}, "Target empty must be selected")
            return {'CANCELLED'}

        try:
            import json
            template_data = json.loads(self.template_data)
            template_name = self.template_name

            # Create new camera
            cam_data = bpy.data.cameras.new(
                name=f"{template_name}_camera")
            cam_obj = bpy.data.objects.new(
                f"{template_name}_camera", cam_data)
            context.scene.collection.objects.link(cam_obj)

            # Set camera as active
            context.scene.camera = cam_obj

            # Apply saved transform
            relative_matrix = Matrix(
                [Vector(row) for row in template_data['relative_transform']])
            cam_obj.matrix_world = props.target_empty.matrix_world @ relative_matrix

            # Apply camera settings
            cam_data.lens = template_data['focal_length']
            cam_data.dof.focus_distance = template_data['dof_distance']

            # Apply constraints
            for constraint_data in template_data['constraints']:
                if constraint_data['type'] == 'TRACK_TO':
                    constraint = cam_obj.constraints.new('TRACK_TO')
                    constraint.target = props.target_empty
                    constraint.track_axis = constraint_data['track_axis']
                    constraint.up_axis = constraint_data['up_axis']

            # Apply animation data
            if template_data.get('animation_data'):
                action_name = f"{template_name}_action"
                action = bpy.data.actions.new(name=action_name)

                # Create location fcurves
                loc_fcurves = [
                    self.create_or_get_fcurve(action, "location", i)
                    for i in range(3)
                ]

                # Apply keyframes
                for kf_data in template_data['animation_data']['keyframes']:
                    frame = kf_data['frame']

                    if kf_data['property'] == 'location':
                        target_matrix = props.target_empty.matrix_world.copy()
                        world_loc = animation_utils.relative_to_world_location(
                            kf_data['value'], target_matrix)

                        for i, value in enumerate(world_loc):
                            point = loc_fcurves[i].keyframe_points.insert(
                                frame, value)
                            point.interpolation = 'BEZIER'
                    else:
                        fcurve = self.create_or_get_fcurve(
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

            self.report(
                {'INFO'}, f"Camera template '{template_name}' applied successfully")
            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Error loading template: {str(e)}")
            return {'CANCELLED'}


class TEMPLATE_OT_RefreshTemplates(Operator):
    """Refresh the list of available templates from the server"""
    bl_idname = "template.refresh_templates"
    bl_label = "Refresh Templates"

    def execute(self, context):
        try:
            # Clear existing templates
            context.scene.server_templates.clear()

            # Get the current template type from the scene
            current_type = context.scene.template_type

            # Fetch templates for the current type
            templates = server_utils.fetch_templates(
                context, template_type=current_type)
            if not templates:
                self.report({'INFO'}, "No templates found")
                return {'FINISHED'}

            # Add templates to the collection
            for template in templates:
                template_item = context.scene.server_templates.add()
                template_item.template_id = str(template['id'])
                template_item.name = template['name']
                template_item.is_public = template['is_public']
                template_item.template_type = template['template_type']
                template_item.template_data = json.dumps(
                    template['templateData'])

            self.report({'INFO'}, f"Found {len(templates)} templates")
            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Error refreshing templates: {str(e)}")
            return {'CANCELLED'}
