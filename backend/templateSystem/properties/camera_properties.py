import bpy
from bpy.types import PropertyGroup
from bpy.props import StringProperty, PointerProperty, BoolProperty


class CameraTemplateProperties(PropertyGroup):
    template_name: StringProperty(
        name="Template Name",
        description="Name for this camera movement template",
        default="New Template"
    )

    target_empty: PointerProperty(
        name="Target Empty",
        type=bpy.types.Object,
        description="Empty object that the camera tracks"
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
    bpy.utils.register_class(CameraTemplateProperties)


def unregister():
    bpy.utils.unregister_class(CameraTemplateProperties)
