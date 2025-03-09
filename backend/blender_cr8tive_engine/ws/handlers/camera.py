"""
Camera command handlers for WebSocket communication.
"""

import logging
from ...core.blender_controllers import BlenderControllers
from ..utils.response_manager import ResponseManager

# Configure logging
logger = logging.getLogger(__name__)


class CameraHandlers:
    """Handlers for camera-related WebSocket commands."""

    # Create a single shared instance of BlenderControllers
    controllers = BlenderControllers()

    # Get a single shared instance of ResponseManager
    response_manager = ResponseManager.get_instance()

    @staticmethod
    def handle_update_camera(data):
        """Handle camera update request"""
        try:
            message_id = data.get('message_id')
            logger.info(
                f"Handling update_camera request with message_id: {message_id}")

            # Extract parameters from the request
            camera_name = data.get('camera_name')

            if not camera_name:
                raise ValueError("Missing camera_name parameter")

            # Update the camera
            result = CameraHandlers.controllers.set_active_camera(camera_name)
            logger.info(f"Camera update result: {result}")

            # Send success response
            CameraHandlers.response_manager.send_response('update_camera_result', True, {
                "success": True,
                "camera_name": camera_name,
                "message": "Camera updated successfully",
                "message_id": message_id
            })

        except Exception as e:
            logger.error(f"Camera update error: {e}")
            import traceback
            traceback.print_exc()
            CameraHandlers.response_manager.send_response('update_camera_result', False, {
                "success": False,
                "message": f"Camera update failed: {str(e)}",
                "message_id": data.get('message_id')
            })
