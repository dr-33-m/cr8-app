# properties/product_template_properties.py

import bpy
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import PropertyGroup


def get_animation_categories(self, context):
    return [
        ('TRANSFORM', "Transform", "Basic transform animations"),
        ('BOUNCE', "Bounce", "Bouncing animations"),
        ('SPIN', "Spin", "Spinning animations"),
        ('FLOAT', "Float", "Floating animations"),
        ('CUSTOM', "Custom", "Custom animations")
    ]


class ProductTemplateProperties(PropertyGroup):
    template_name: StringProperty(
        name="Template Name",
        description="Name for this animation template",
        default="New Animation"
    )

    animation_category: EnumProperty(
        name="Category",
        description="Category of the animation",
        items=get_animation_categories
    )

    is_public: BoolProperty(
        name="Public Template",
        description="Make this template available to all users",
        default=True
    )

    thumbnail_path: StringProperty(
        name="Thumbnail Path",
        description="Path to the thumbnail image",
        default="",
        subtype='FILE_PATH'
    )


def register():
    bpy.utils.register_class(ProductTemplateProperties)


def unregister():
    bpy.utils.unregister_class(ProductTemplateProperties)
