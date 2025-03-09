"""
Material command handlers for WebSocket communication.
"""

import logging
from ...core.blender_controllers import BlenderControllers
from ..utils.response_manager import ResponseManager

# Configure logging
logger = logging.getLogger(__name__)


class MaterialHandlers:
    """Handlers for material-related WebSocket commands."""

    # Create a single shared instance of BlenderControllers
    controllers = BlenderControllers()

    # Get a single shared instance of ResponseManager
    response_manager = ResponseManager.get_instance()

    @staticmethod
    def handle_update_material(data):
        """Handle material update request"""
        try:
            message_id = data.get('message_id')
            logger.info(
                f"Handling update_material request with message_id: {message_id}")

            # Extract parameters from the request
            material_name = data.get('material_name')
            color = data.get('color')
            roughness = data.get('roughness')
            metallic = data.get('metallic')

            if not material_name:
                raise ValueError("Missing material_name parameter")

            # Update the material
            result = MaterialHandlers.controllers.update_material(
                material_name,
                color=color,
                roughness=roughness,
                metallic=metallic
            )
            logger.info(f"Material update result: {result}")

            # Send success response
            MaterialHandlers.response_manager.send_response('update_material_result', True, {
                "success": True,
                "material_name": material_name,
                "message": "Material updated successfully",
                "message_id": message_id
            })

        except Exception as e:
            logger.error(f"Material update error: {e}")
            import traceback
            traceback.print_exc()
            MaterialHandlers.response_manager.send_response('update_material_result', False, {
                "success": False,
                "message": f"Material update failed: {str(e)}",
                "message_id": data.get('message_id')
            })
