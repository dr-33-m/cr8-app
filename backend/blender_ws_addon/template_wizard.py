import bpy


class TemplateWizard:
    @staticmethod
    def scan_controllable_objects():
        """
        Scan the current Blender scene for objects with 'controllable_' prefix
        Returns a dictionary of controllable objects categorized by type.
        Handles lights, cameras, materials, and objects.
        """
        controllables = {
            'cameras': [
                {'name': camera.name, 'supported_controls': [
                    'activate', 'settings']}
                for camera in bpy.data.cameras if camera.name.startswith('controllable_')
            ],
            'lights': [
                {'name': light.name, 'type': light.type,
                    'supported_controls': ['color', 'strength', 'temperature']}
                for light in bpy.data.lights if light.name.startswith('controllable_')
            ],
            'materials': [
                {'name': material.name, 'supported_controls': [
                    'color', 'roughness', 'metallic']}
                for material in bpy.data.materials if material.name.startswith('controllable_')
            ],
            'objects': [
                {'name': obj.name, 'type': obj.type, 'supported_controls': [
                    'location', 'rotation', 'scale']}
                for obj in bpy.data.objects if obj.name.startswith('controllable_')
            ]
        }

        return controllables


def register():
    """Register module (if needed)"""
    pass


def unregister():
    """Unregister module (if needed)"""
    pass
