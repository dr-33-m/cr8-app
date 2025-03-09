"""
Scene command handlers for WebSocket communication.
This includes camera, light, material, and object transformation handlers.
"""

import logging
import bpy
from ...core.blender_controllers import BlenderControllers
from ..utils.response_manager import ResponseManager

# Configure logging
logger = logging.getLogger(__name__)


class SceneHandlers:
    """Handlers for scene-related WebSocket commands."""

    # Create a single shared instance of BlenderControllers
    controllers = BlenderControllers()

    # Get a single shared instance of ResponseManager
    response_manager = ResponseManager.get_instance()

    @staticmethod
    def handle_camera_change(data):
        """Handle changing the active camera"""
        try:
            message_id = data.get('message_id')
            logger.info(
                f"Handling camera change request with message_id: {message_id}")

            # Extract parameters from the request
            camera_name = data.get('camera_name')

            # Call the controllers to change the camera
            result = SceneHandlers.controllers.set_active_camera(camera_name)

            logger.info(f"Camera change result: {result}")

            # Send response with the result
            SceneHandlers.response_manager.send_response('camera_change_result', result, {
                "message": f"Camera changed to {camera_name}" if result else f"Failed to change camera to {camera_name}",
                "message_id": message_id
            })

        except Exception as e:
            logger.error(f"Error during camera change: {e}")
            import traceback
            traceback.print_exc()
            SceneHandlers.response_manager.send_response('camera_change_result', False, {
                "message": str(e),
                "message_id": data.get('message_id')
            })

    @staticmethod
    def handle_light_update(data):
        """Handle updating a light's properties"""
        try:
            message_id = data.get('message_id')
            logger.info(
                f"Handling light update request with message_id: {message_id}")

            # Extract parameters from the request
            light_name = data.get('light_name')
            color = data.get('color')
            strength = data.get('strength')

            # Call the controllers to update the light
            result = SceneHandlers.controllers.update_light(
                light_name, color=color, strength=strength)

            logger.info(f"Light update result: {result}")

            # Send response with the result
            SceneHandlers.response_manager.send_response('light_update_result', result, {
                "message": f"Light {light_name} updated" if result else f"Failed to update light {light_name}",
                "message_id": message_id
            })

        except Exception as e:
            logger.error(f"Error during light update: {e}")
            import traceback
            traceback.print_exc()
            SceneHandlers.response_manager.send_response('light_update_result', False, {
                "message": str(e),
                "message_id": data.get('message_id')
            })

    @staticmethod
    def handle_material_update(data):
        """Handle updating a material's properties"""
        try:
            message_id = data.get('message_id')
            logger.info(
                f"Handling material update request with message_id: {message_id}")

            # Extract parameters from the request
            material_name = data.get('material_name')
            color = data.get('color')
            roughness = data.get('roughness')
            metallic = data.get('metallic')

            # Call the controllers to update the material
            result = SceneHandlers.controllers.update_material(
                material_name, color=color, roughness=roughness, metallic=metallic)

            logger.info(f"Material update result: {result}")

            # Send response with the result
            SceneHandlers.response_manager.send_response('material_update_result', result, {
                "message": f"Material {material_name} updated" if result else f"Failed to update material {material_name}",
                "message_id": message_id
            })

        except Exception as e:
            logger.error(f"Error during material update: {e}")
            import traceback
            traceback.print_exc()
            SceneHandlers.response_manager.send_response('material_update_result', False, {
                "message": str(e),
                "message_id": data.get('message_id')
            })

    @staticmethod
    def handle_object_transformation(data):
        """Handle transforming an object (location, rotation, scale)"""
        try:
            message_id = data.get('message_id')
            logger.info(
                f"Handling object transformation request with message_id: {message_id}")

            # Extract parameters from the request
            object_name = data.get('object_name')
            location = data.get('location')
            rotation = data.get('rotation')
            scale = data.get('scale')

            # Call the controllers to update the object
            result = SceneHandlers.controllers.update_object(
                object_name, location=location, rotation=rotation, scale=scale)

            logger.info(f"Object transformation result: {result}")

            # Send response with the result
            SceneHandlers.response_manager.send_response('object_transformation_result', result, {
                "message": f"Object {object_name} transformed" if result else f"Failed to transform object {object_name}",
                "message_id": message_id
            })

        except Exception as e:
            logger.error(f"Error during object transformation: {e}")
            import traceback
            traceback.print_exc()
            SceneHandlers.response_manager.send_response('object_transformation_result', False, {
                "message": str(e),
                "message_id": data.get('message_id')
            })
