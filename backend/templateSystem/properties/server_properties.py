import bpy
from bpy.types import PropertyGroup
from bpy.props import StringProperty, BoolProperty, EnumProperty


class ServerTemplateItem(PropertyGroup):
    """Properties for a template stored on the server"""
    template_id: StringProperty(
        name="Template ID",
        description="Unique identifier for the template"
    )
    name: StringProperty(
        name="Name",
        description="Template name"
    )
    is_public: BoolProperty(
        name="Public",
        description="Whether this template is public",
        default=True
    )
    template_data: StringProperty(
        name="Template Data",
        description="JSON string of template data"
    )
    template_type: EnumProperty(
        items=[
            ("camera", "Camera", "Camera template"),
            ("light", "Light", "Light template"),
            ("product", "Product", "Product template")
        ],
        name="Template Type",
        description="Type of the template"
    )


def register():
    bpy.utils.register_class(ServerTemplateItem)


def unregister():
    bpy.utils.unregister_class(ServerTemplateItem)
