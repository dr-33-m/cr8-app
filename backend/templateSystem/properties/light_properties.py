import bpy
from bpy.types import PropertyGroup
from bpy.props import StringProperty, PointerProperty, BoolProperty, CollectionProperty


class LightTemplateProperties(PropertyGroup):
    template_name: StringProperty(
        name="Template Name",
        description="Name for this lighting setup template",
        default="New Light Setup"
    )

    target_empty: PointerProperty(
        name="Target Empty",
        type=bpy.types.Object,
        description="Empty object that the lights will be positioned relative to"
    )

    selected_lights: CollectionProperty(
        type=bpy.types.PropertyGroup,
        name="Selected Lights",
        description="Lights to include in the template"
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
    bpy.utils.register_class(LightTemplateProperties)


def unregister():
    bpy.utils.unregister_class(LightTemplateProperties)
