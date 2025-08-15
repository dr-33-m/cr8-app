import bpy
import os
import json
from bpy.types import Panel
from ..operators import cameras, lights
from ..properties import CameraTemplateProperties
from ..utils.path_utils import get_template_path


class VIEW3D_PT_TemplateSystem(Panel):
    """Base Template System Panel"""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Template System'
    bl_label = "Template System"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Add template type selector
        row = layout.row()
        row.prop(scene, "template_type", expand=True)


class VIEW3D_PT_CameraTemplates(Panel):
    """Camera Template System Panel"""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Template System'
    bl_label = "Camera Templates"
    bl_parent_id = "VIEW3D_PT_TemplateSystem"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.template_type == 'CAMERA'

    def draw(self, context):
        layout = self.layout
        props = context.scene.camera_template_props

        # Template Name
        layout.prop(props, "template_name")

        # Target Empty
        layout.prop(props, "target_empty")

        # Thumbnail
        layout.prop(props, "thumbnail_path")

        # Public/Private setting
        layout.prop(props, "is_public")

        # Save Template
        layout.operator("template.save_camera")

        # Template List Section
        box = layout.box()
        box.label(text="Available Camera Templates")

        # Refresh button
        row = box.row()
        row.operator("template.refresh_templates",
                     text="Refresh Templates", icon='FILE_REFRESH')

        # List templates
        found_templates = False
        for template in context.scene.server_templates:
            try:
                if template.template_type == 'camera':
                    found_templates = True
                    row = box.row(align=True)
                    # Template name
                    row.label(text=template.name)
                    # Load button
                    op = row.operator(
                        "template.load_server_camera",
                        text="Load",
                        icon='IMPORT'
                    )
                    op.template_id = template.template_id
                    op.template_data = template.template_data
                    op.template_name = template.name
            except Exception as e:
                print(f"Error displaying template {template.name}: {str(e)}")
                continue

        if not found_templates:
            box.label(text="No camera templates found", icon='INFO')


class VIEW3D_PT_LightTemplates(Panel):
    """Light Template System Panel"""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Template System'
    bl_label = "Light Templates"
    bl_parent_id = "VIEW3D_PT_TemplateSystem"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.template_type == 'LIGHT'

    def draw(self, context):
        layout = self.layout
        props = context.scene.light_template_props

        # Template Name
        layout.prop(props, "template_name")

        # Target Empty
        layout.prop(props, "target_empty")

        # Selected Lights Info
        box = layout.box()
        box.label(text="Selected Lights")
        selected_lights = [
            obj for obj in context.selected_objects if obj.type == 'LIGHT']
        if selected_lights:
            for light in selected_lights:
                box.label(text=light.name, icon='LIGHT')
        else:
            box.label(text="No lights selected", icon='ERROR')

        # Thumbnail
        layout.prop(props, "thumbnail_path")

        # Public/Private setting
        layout.prop(props, "is_public")

        # Save Template
        layout.operator("template.save_light_setup")

        # Template List Section
        box = layout.box()
        box.label(text="Available Light Templates")

        # Refresh button
        row = box.row()
        row.operator("template.refresh_templates",
                     text="Refresh Templates", icon='FILE_REFRESH')

        # List templates
        found_templates = False
        for template in context.scene.server_templates:
            try:
                if template.template_type == 'light':
                    found_templates = True
                    row = box.row(align=True)
                    # Template name
                    row.label(text=template.name)
                    # Load button
                    op = row.operator(
                        "template.load_light_setup",
                        text="Load",
                        icon='IMPORT'
                    )
                    op.template_id = template.template_id
                    op.template_data = template.template_data
                    op.template_name = template.name
            except Exception as e:
                print(f"Error displaying template {template.name}: {str(e)}")
                continue

        if not found_templates:
            box.label(text="No light templates found", icon='INFO')


class VIEW3D_PT_ProductTemplates(Panel):
    """Product Animation Template System Panel"""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Template System'
    bl_label = "Product Animations"
    bl_parent_id = "VIEW3D_PT_TemplateSystem"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.template_type == 'PRODUCT'

    def draw(self, context):
        layout = self.layout
        props = context.scene.product_template_props

        # Selected Object Info
        box = layout.box()
        box.label(text="Selected Object")

        if context.active_object:
            box.label(text=context.active_object.name, icon='OBJECT_DATA')

            # Determine if we're dealing with an empty or a product
            if context.active_object.type == 'EMPTY':
                # For empties, check if they have children
                has_children = False
                for obj in bpy.data.objects:
                    if obj.parent == context.active_object:
                        has_children = True
                        break

                if has_children:
                    box.label(text="Empty with children",
                              icon='OUTLINER_OB_GROUP_INSTANCE')
                else:
                    box.label(text="Warning: Empty has no children",
                              icon='ERROR')
            else:
                # For other objects, check if they have a parent empty
                if context.active_object.parent and context.active_object.parent.type == 'EMPTY':
                    box.label(
                        text=f"Parent: {context.active_object.parent.name}", icon='EMPTY_DATA')
                else:
                    box.label(text="Note: No parent empty", icon='INFO')
                    box.label(text="Parent empty will be created",
                              icon='OUTLINER_DATA_EMPTY')
        else:
            box.label(text="No object selected", icon='ERROR')

        # Template Name and Category
        layout.prop(props, "template_name")
        layout.prop(props, "animation_category")

        # Thumbnail
        layout.prop(props, "thumbnail_path")

        # Public/Private setting
        layout.prop(props, "is_public")

        # Save Template
        layout.operator("template.save_product_animation")

        # Template List Section
        box = layout.box()
        box.label(text="Available Animations")

        # Refresh button
        row = box.row()
        row.operator("template.refresh_templates",
                     text="Refresh", icon='FILE_REFRESH')

        # List templates by category
        found_templates = False
        current_category = None

        for template in context.scene.server_templates:
            try:
                if template.template_type == 'product':
                    template_data = json.loads(template.template_data)
                    category = template_data.get('category', 'CUSTOM')

                    # Add category header if changed
                    if category != current_category:
                        box.label(
                            text=f"▼ {category.title()} Animations", icon='DISCLOSURE_TRI_DOWN')
                        current_category = category

                    found_templates = True
                    row = box.row(align=True)
                    # Template name
                    row.label(text=template.name)
                    # Load button
                    op = row.operator(
                        "template.load_product_animation",
                        text="Apply",
                        icon='IMPORT'
                    )
                    op.template_id = template.template_id
                    op.template_data = template.template_data
                    op.template_name = template.name
            except Exception as e:
                print(f"Error displaying template {template.name}: {str(e)}")
                continue

        if not found_templates:
            box.label(text="No animations found", icon='INFO')
