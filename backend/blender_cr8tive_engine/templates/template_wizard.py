import bpy


class TemplateWizard:
    def get_template_controls(self):
        """
        Get all template controls by scanning for controllable objects

        Returns:
            List of control objects that can be manipulated
        """
        # Use the existing scan method
        controllables = self.scan_controllable_objects()

        # Convert to a list of controls
        controls = []

        # Process cameras
        for camera in controllables.get('cameras', []):
            controls.append({
                'id': camera['name'],
                'type': 'camera',
                'name': camera['name'],
                'displayName': camera['name'].replace('controllable_', ''),
                'supported_controls': camera['supported_controls']
            })

        # Process lights
        for light in controllables.get('lights', []):
            controls.append({
                'id': light['name'],
                'type': 'light',
                'name': light['name'],
                'displayName': light['name'].replace('controllable_', ''),
                'light_type': light['type'],
                'supported_controls': light['supported_controls']
            })

        # Process materials
        for material in controllables.get('materials', []):
            controls.append({
                'id': material['name'],
                'type': 'material',
                'name': material['name'],
                'displayName': material['name'].replace('controllable_', ''),
                'supported_controls': material['supported_controls']
            })

        # Process objects
        for obj in controllables.get('objects', []):
            controls.append({
                'id': obj['name'],
                'type': 'object',
                'name': obj['name'],
                'displayName': obj['name'].replace('controllable_', ''),
                'object_type': obj['type'],
                'supported_controls': obj['supported_controls']
            })

        return controls

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
