import bpy
from bpy.props import PointerProperty, CollectionProperty, StringProperty, EnumProperty
from .properties import register as register_properties, unregister as unregister_properties
from .properties.camera_properties import CameraTemplateProperties
from .properties.light_properties import LightTemplateProperties
from .properties.server_properties import ServerTemplateItem
from .properties.product_properties import ProductTemplateProperties
from .operators import cameras, lights, products
from .panels import VIEW3D_PT_TemplateSystem, VIEW3D_PT_CameraTemplates, VIEW3D_PT_LightTemplates, VIEW3D_PT_ProductTemplates

bl_info = {
    "name": "Cr8-xyz Animation Engine",
    "author": "Thamsanqa J Ncube",
    "version": (1, 0),
    "blender": (4, 3, 2),
    "location": "View3D > Sidebar > Template System",
    "description": "Create Reusable animations for Users of Cr8-xyz",
    "category": "Animation",
}


def template_type_update(self, context):
    if context.area:
        context.area.tag_redraw()


class CAMERATEMPLATE_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    user_id: StringProperty(
        name="User ID",
        default="",
        description="Your user ID for template synchronization"
    )

    api_url: StringProperty(
        name="API URL",
        default="http://localhost:8000/api/v1",
        description="URL of the Cr8 Engine Server"
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "user_id")
        layout.prop(self, "api_url")


classes = (
    CAMERATEMPLATE_AddonPreferences,
    cameras.TEMPLATE_OT_SaveCamera,
    cameras.TEMPLATE_OT_LoadServerCamera,
    cameras.TEMPLATE_OT_RefreshTemplates,
    lights.TEMPLATE_OT_SaveLightSetup,
    lights.TEMPLATE_OT_LoadLightSetup,
    products.TEMPLATE_OT_SaveProductAnimation,
    products.TEMPLATE_OT_LoadProductAnimation,
    VIEW3D_PT_TemplateSystem,
    VIEW3D_PT_CameraTemplates,
    VIEW3D_PT_LightTemplates,
    VIEW3D_PT_ProductTemplates
)


def register():
    # Register properties first
    register_properties()

    # Register other classes
    for cls in classes:
        bpy.utils.register_class(cls)

    # Register template type property
    bpy.types.Scene.template_type = EnumProperty(
        name="Template Type",
        items=[
            ('CAMERA', "Camera", "Camera templates"),
            ('LIGHT', "Light", "Light templates"),
            ('PRODUCT', "Product", "Product templates")
        ],
        default='CAMERA',
        update=template_type_update
    )

    # Register property group assignments
    bpy.types.Scene.camera_template_props = PointerProperty(
        type=CameraTemplateProperties)
    bpy.types.Scene.light_template_props = PointerProperty(
        type=LightTemplateProperties)
    bpy.types.Scene.server_templates = CollectionProperty(
        type=ServerTemplateItem)
    bpy.types.Scene.product_template_props = PointerProperty(
        type=ProductTemplateProperties)


def unregister():
    # Unregister property group assignments
    if hasattr(bpy.types.Scene, 'server_templates'):
        del bpy.types.Scene.server_templates
    if hasattr(bpy.types.Scene, 'camera_template_props'):
        del bpy.types.Scene.camera_template_props
    if hasattr(bpy.types.Scene, 'light_template_props'):
        del bpy.types.Scene.light_template_props
    if hasattr(bpy.types.Scene, "template_type"):
        del bpy.types.Scene.template_type

    # Unregister classes in reverse order
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass

    # Unregister properties last
    unregister_properties()
