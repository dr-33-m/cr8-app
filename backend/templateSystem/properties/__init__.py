from .camera_properties import CameraTemplateProperties, register as register_cam, unregister as unregister_cam
from .light_properties import LightTemplateProperties, register as register_light, unregister as unregister_light
from .server_properties import ServerTemplateItem, register as register_server, unregister as unregister_server
from .product_properties import register as register_product, unregister as unregister_product


def register():
    register_cam()
    register_light()
    register_server()
    register_product()


def unregister():
    unregister_server()
    unregister_light()
    unregister_cam()
    unregister_product()
