"""
Object command handlers for WebSocket communication.
"""

import logging
from ...core.blender_controllers import BlenderControllers
from ..utils.response_manager import ResponseManager

# Configure logging
logger = logging.getLogger(__name__)


class ObjectHandlers:
    """Handlers for object-related WebSocket commands."""

    # Create a single shared instance of BlenderControllers
    controllers = BlenderControllers()

    # Get a single shared instance of ResponseManager
    response_manager = ResponseManager.get_instance()

    @staticmethod
    def handle_update_object(data):
        """Handle object update request"""
        try:
            message_id = data.get('message_id')
            logger.info(
                f"Handling update_object request with message_id: {message_id}")

            # Extract parameters from the request
            object_name = data.get('object_name')
            location = data.get('location')
            rotation = data.get('rotation')
            scale = data.get('scale')

            if not object_name:
                raise ValueError("Missing object_name parameter")

            # Update the object
            result = ObjectHandlers.controllers.update_object(
                object_name,
                location=location,
                rotation=rotation,
                scale=scale
            )
            logger.info(f"Object update result: {result}")

            # Send success response
            ObjectHandlers.response_manager.send_response('update_object_result', True, {
                "success": True,
                "object_name": object_name,
                "message": "Object updated successfully",
                "message_id": message_id
            })

        except Exception as e:
            logger.error(f"Object update error: {e}")
            import traceback
            traceback.print_exc()
            ObjectHandlers.response_manager.send_response('update_object_result', False, {
                "success": False,
                "message": f"Object update failed: {str(e)}",
                "message_id": data.get('message_id')
            })
