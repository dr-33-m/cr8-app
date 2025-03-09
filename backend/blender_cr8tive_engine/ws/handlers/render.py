"""
Rendering command handlers for WebSocket communication.
"""

import logging
import bpy
import os
from pathlib import Path
from ...rendering.video_generator import GenerateVideo
from ...rendering.preview_renderer import get_preview_renderer
from ...core.blender_controllers import BlenderControllers
from ..utils.session_manager import SessionManager
from ..utils.response_manager import ResponseManager

# Configure logging
logger = logging.getLogger(__name__)


class RenderHandlers:
    """Handlers for rendering-related WebSocket commands."""

    # Create a single shared instance of BlenderControllers
    controllers = BlenderControllers()

    # Get a single shared instance of ResponseManager
    response_manager = ResponseManager.get_instance()

    @staticmethod
    def handle_preview_rendering(data):
        """Handle preview rendering request"""
        try:
            message_id = data.get('message_id')
            logger.info(
                f"Handling preview rendering request with message_id: {message_id}")

            # Extract parameters from the request
            params = data.get('params', {})

            # Get username from SessionManager
            session_manager = SessionManager.get_instance()
            username = session_manager.get_username()

            # Get the preview renderer
            preview_renderer = get_preview_renderer(username)

            # Cleanup any existing preview frames
            preview_renderer.cleanup()

            # Setup preview render settings
            preview_renderer.setup_preview_render(params)

            # Render the entire animation once
            bpy.ops.render.opengl(animation=True)

            # Send success response
            RenderHandlers.response_manager.send_response('start_broadcast', True, {
                "message": "Preview rendering started",
                "message_id": message_id
            })

        except Exception as e:
            logger.error(f"Preview rendering error: {e}")
            import traceback
            traceback.print_exc()
            RenderHandlers.response_manager.send_response('start_broadcast', False, {
                "message": f"Preview rendering failed: {str(e)}",
                "message_id": data.get('message_id')
            })

    @staticmethod
    def handle_generate_video(data):
        """Handle video generation request"""
        try:
            message_id = data.get('message_id')
            logger.info(
                f"Handling generate video request with message_id: {message_id}")

            # Get username from SessionManager
            session_manager = SessionManager.get_instance()
            username = session_manager.get_username()

            # Set up paths
            image_sequence_directory = Path(
                f"/mnt/shared_storage/Cr8tive_Engine/Sessions/{username}") / "preview"
            output_file = image_sequence_directory / "preview.mp4"
            resolution = (1280, 720)
            fps = 30

            # Ensure the directory exists
            image_sequence_directory.mkdir(parents=True, exist_ok=True)

            # Check if there are actually image files in the directory
            image_files = list(image_sequence_directory.glob('*.png'))
            if not image_files:
                raise ValueError(
                    "No image files found in the specified directory")

            # Initialize and execute the handler
            video_generator = GenerateVideo(
                str(image_sequence_directory),
                str(output_file),
                resolution,
                fps
            )
            video_generator.gen_video_from_images()

            # Send success response
            RenderHandlers.response_manager.send_response('generate_video', True, {
                "success": True,
                "status": "completed",
                "message": "Video generation completed successfully",
                "output_file": str(output_file),
                "message_id": message_id
            })

        except Exception as e:
            error_message = str(e)
            logger.error(
                f"Video generation error: {error_message}"
            )
            import traceback
            traceback.print_exc()

            # Send error response
            RenderHandlers.response_manager.send_response('generate_video', False, {
                "success": False,
                "status": "failed",
                "message": f"Video generation failed: {error_message}",
                "message_id": data.get('message_id')
            })
