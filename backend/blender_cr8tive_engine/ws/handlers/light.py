"""
Light command handlers for WebSocket communication.
"""

import logging
from ...core.blender_controllers import BlenderControllers
from ..utils.response_manager import ResponseManager

# Configure logging
logger = logging.getLogger(__name__)


class LightHandlers:
    """Handlers for light-related WebSocket commands."""

    # Create a single shared instance of BlenderControllers
    controllers = BlenderControllers()

    # Get a single shared instance of ResponseManager
    response_manager = ResponseManager.get_instance()

    @staticmethod
    def handle_update_light(data):
        """Handle light update request"""
        try:
            message_id = data.get('message_id')
            logger.info(
                f"Handling update_light request with message_id: {message_id}")

            # Extract parameters from the request
            light_name = data.get('light_name')
            color = data.get('color')
            strength = data.get('strength')

            if not light_name:
                raise ValueError("Missing light_name parameter")

            # Update the light
            result = LightHandlers.controllers.update_light(
                light_name,
                color=color,
                strength=strength
            )
            logger.info(f"Light update result: {result}")

            # Send success response
            LightHandlers.response_manager.send_response('update_light_result', True, {
                "success": True,
                "light_name": light_name,
                "message": "Light updated successfully",
                "message_id": message_id
            })

        except Exception as e:
            logger.error(f"Light update error: {e}")
            import traceback
            traceback.print_exc()
            LightHandlers.response_manager.send_response('update_light_result', False, {
                "success": False,
                "message": f"Light update failed: {str(e)}",
                "message_id": data.get('message_id')
            })
