import bpy
import mathutils
from ..rendering.preview_renderer import get_preview_renderer


class BlenderControllers:
    @staticmethod
    def set_active_camera(camera_name):
        """Set a specific camera as active in the scene"""
        try:
            camera = bpy.data.objects.get(camera_name)
            if camera and camera.type == 'CAMERA':
                bpy.context.scene.camera = camera
                for area in bpy.context.screen.areas:
                    if area.type == 'VIEW_3D':
                        area.spaces[0].region_3d.view_perspective = 'CAMERA'
                        break
                return True
            return False
        except Exception as e:
            print(f"Error setting active camera: {e}")
            return False

    @staticmethod
    def update_light(light_name, color=None, strength=None):
        """Update light properties such as color, strength."""
        try:
            light_object = bpy.data.objects.get(light_name)
            if light_object and light_object.type == 'LIGHT':
                light_data = light_object.data

                if color is not None:
                    if isinstance(color, str):
                        # Convert hex to RGB
                        color = tuple(
                            int(color[i:i+2], 16) / 255.0 for i in (1, 3, 5))
                    light_data.color = color
                if strength is not None:
                    light_data.energy = strength

                return True
            return False
        except Exception as e:
            print(f"Error updating light: {e}")
            return False

    @staticmethod
    def update_material(material_name, color=None, roughness=None, metallic=None):
        """Update material properties like color, roughness, and metallic"""
        try:
            material = bpy.data.materials.get(material_name)
            if material:
                principled_node = next(
                    (node for node in material.node_tree.nodes if node.type == 'BSDF_PRINCIPLED'), None)

                if principled_node:
                    if color is not None:
                        principled_node.inputs['Base Color'].default_value = color
                    if roughness is not None:
                        principled_node.inputs['Roughness'].default_value = roughness
                    if metallic is not None:
                        principled_node.inputs['Metallic'].default_value = metallic

                return True
            return False
        except Exception as e:
            print(f"Error updating material: {e}")
            return False

    @staticmethod
    def update_object(object_name, location=None, rotation=None, scale=None):
        """Update object properties like location, rotation, and scale"""
        try:
            obj = bpy.data.objects.get(object_name)
            if obj:
                if location is not None:
                    obj.location = mathutils.Vector(location)
                if rotation is not None:
                    obj.rotation_euler = mathutils.Euler(rotation, 'XYZ')
                if scale is not None:
                    obj.scale = mathutils.Vector(scale)

                return True
            return False
        except Exception as e:
            print(f"Error updating object: {e}")
            return False

    @staticmethod
    def create_preview_renderer(username):
        """Create and return a preview renderer instance with the given username"""
        return get_preview_renderer(username)
