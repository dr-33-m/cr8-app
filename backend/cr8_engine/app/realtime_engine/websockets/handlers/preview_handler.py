"""
Preview and rendering handlers for WebSocket communication in cr8_engine.
"""

import asyncio
import base64
import logging
import uuid
from pathlib import Path
from typing import Dict, Any
from .base_specialized_handler import BaseSpecializedHandler

# Configure logging
logger = logging.getLogger(__name__)


class PreviewHandler(BaseSpecializedHandler):
    """Handlers for preview-related WebSocket commands."""

    def __init__(self, session_manager):
        """
        Initialize the preview handler.

        Args:
            session_manager: The session manager instance
        """
        super().__init__(session_manager)

    def _get_preview_dir(self, username: str):
        """
        Get the preview directory for a specific user.

        Args:
            username: The username of the client

        Returns:
            Path: The path to the user's preview directory
        """
        # Define the base directory where previews are stored
        base_preview_dir = Path("/tmp/blender_renders")

        # Create a user-specific directory dynamically
        user_preview_dir = base_preview_dir / username / "preview"

        # Ensure the directory exists
        user_preview_dir.mkdir(exist_ok=True, parents=True)

        return user_preview_dir

    async def handle_preview_rendering(self, username: str, data: Dict[str, Any], client_type: str) -> None:
        """
        Handle preview rendering requests.

        Args:
            username: The username of the client
            data: The message data
            client_type: The type of client (browser or blender)
        """
        if client_type != "browser":
            return

        try:
            self.logger.info(
                f"Handling preview rendering request from {username}")

            # Generate message_id
            message_id = str(uuid.uuid4())
            self.logger.debug(f"Generated message_id: {message_id}")

            # Forward the command to Blender
            try:
                # Add to pending requests for tracking
                self.session_manager.add_pending_request(username, message_id)

                # Forward to Blender
                session = await self.forward_to_blender(
                    username,
                    'start_preview_rendering',
                    {
                        'params': data.get('params', {})
                    },
                    message_id
                )

                # Send confirmation to browser
                await self.send_response(
                    username,
                    'preview_rendering_result',
                    True,
                    {
                        'status': 'forwarded_to_blender'
                    },
                    "Preview rendering started",
                    message_id
                )

            except ValueError as ve:
                await self.send_error(username, 'preview_rendering', str(ve), message_id)

        except Exception as e:
            self.logger.error(f"Error handling preview rendering: {e}")
            import traceback
            traceback.print_exc()
            await self.send_error(username, 'preview_rendering', f"Error: {str(e)}", data.get('message_id'))

    async def handle_generate_video(self, username: str, data: Dict[str, Any], client_type: str) -> None:
        """
        Handle video generation requests.

        Args:
            username: The username of the client
            data: The message data
            client_type: The type of client (browser or blender)
        """
        if client_type != "browser":
            return

        try:
            self.logger.info(
                f"Handling generate video request from {username}")

            # Generate message_id
            message_id = str(uuid.uuid4())
            self.logger.debug(f"Generated message_id: {message_id}")

            # Forward the command to Blender
            try:
                # Forward to Blender
                session = await self.forward_to_blender(
                    username,
                    'generate_video',
                    data,
                    message_id
                )

                # Send confirmation to browser
                await self.send_response(
                    username,
                    'generate_video_result',
                    True,
                    {
                        'status': 'forwarded_to_blender'
                    },
                    "Video generation started",
                    message_id
                )

            except ValueError as ve:
                await self.send_error(username, 'generate_video', str(ve), message_id)

        except Exception as e:
            self.logger.error(f"Error handling generate video: {e}")
            import traceback
            traceback.print_exc()
            await self.send_error(username, 'generate_video', f"Error: {str(e)}", data.get('message_id'))

    async def handle_start_broadcast(self, username: str, data: Dict[str, Any], client_type: str) -> None:
        """
        Handle starting frame broadcasting.

        Args:
            username: The username of the client
            data: The message data
            client_type: The type of client (browser or blender)
        """
        try:
            self.logger.info(
                f"Handling start broadcast request from {username}")

            session = self.session_manager.get_session(username)
            if not session:
                self.logger.error(f"No session found for {username}")
                return

            # Do not reset last_frame_index; resume from where it left off
            session.should_broadcast = True

            # Create new task only if none exists or previous completed
            if not hasattr(session, 'broadcast_task') or session.broadcast_task.done():
                session.broadcast_task = asyncio.create_task(
                    self._broadcast_frames(username)
                )

            # Notify client
            if session.browser_socket:
                await session.browser_socket.send_json({
                    "status": "OK",
                    "message": "Frame broadcast started/resumed"
                })

        except Exception as e:
            self.logger.error(f"Error handling start broadcast: {e}")
            import traceback
            traceback.print_exc()
            await self.send_error(username, 'start_broadcast', f"Error: {str(e)}", data.get('message_id'))

    async def handle_stop_broadcast(self, username: str, data: Dict[str, Any], client_type: str) -> None:
        """
        Handle stopping frame broadcasting.

        Args:
            username: The username of the client
            data: The message data
            client_type: The type of client (browser or blender)
        """
        try:
            self.logger.info(
                f"Handling stop broadcast request from {username}")

            session = self.session_manager.get_session(username)
            if not session:
                self.logger.error(f"No session found for {username}")
                return

            # Set flag to break broadcast loop
            session.should_broadcast = False

            # Cancel task if running
            if hasattr(session, 'broadcast_task'):
                if not session.broadcast_task.done():
                    session.broadcast_task.cancel()
                    try:
                        await session.broadcast_task  # Handle cleanup
                    except asyncio.CancelledError:
                        self.logger.info(f"Broadcast stopped for {username}")
                    except Exception as e:
                        self.logger.error(f"Error stopping broadcast: {e}")

            # Notify client
            if session.browser_socket:
                await session.browser_socket.send_json({
                    "status": "OK",
                    "message": "Frame broadcast stopped"
                })

        except Exception as e:
            self.logger.error(f"Error handling stop broadcast: {e}")
            import traceback
            traceback.print_exc()
            await self.send_error(username, 'stop_broadcast', f"Error: {str(e)}", data.get('message_id'))

    async def _broadcast_frames(self, username: str):
        """
        Broadcast frames once (stops after last frame).

        Args:
            username: The username of the client
        """
        session = self.session_manager.get_session(username)
        if not session or not session.browser_socket:
            return

        # Get the preview directory for this user
        preview_dir = self._get_preview_dir(username)

        try:
            frames = sorted(preview_dir.glob("frame_*.png"))
            if not frames:
                return

            # Start from the frame after the last frame that was sent
            start_frame_index = session.last_frame_index + \
                1 if session.last_frame_index is not None else 0

            # Broadcast frames sequentially (no automatic looping)
            for frame_index in range(start_frame_index, len(frames)):
                frame = frames[frame_index]

                if not session.should_broadcast:  # Check pause/stop flag
                    break

                try:
                    with open(frame, "rb") as img_file:
                        img_str = base64.b64encode(img_file.read()).decode()
                        await session.browser_socket.send_json({
                            "type": "frame",
                            "data": img_str,
                            "frame_index": frame_index,
                        })
                    session.last_frame_index = frame_index  # Track progress
                except Exception as e:
                    self.logger.error(f"Error sending frame: {e}")
                    session.should_broadcast = False
                    return

                await asyncio.sleep(0.033)  # ~30 FPS

            # Notify client the broadcast finished (only if it completed fully)
            if session.last_frame_index == len(frames) - 1:
                await session.browser_socket.send_json({
                    "type": "broadcast_complete"
                })
                # Reset last_frame_index only after the last frame has been sent
                session.last_frame_index = -1

        except asyncio.CancelledError:
            self.logger.info(f"Broadcast cancelled for {username}")
        except Exception as e:
            self.logger.error(f"Broadcast error: {e}")
        finally:
            session.should_broadcast = False  # Ensure broadcast stops
