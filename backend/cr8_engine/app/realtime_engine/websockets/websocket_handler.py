# app/websockets/websocket_handler.py
import asyncio
import logging
import base64
from typing import Dict, Any, Optional
from pathlib import Path
import uuid
from fastapi import WebSocket
from app.core.config import settings


class WebSocketHandler:
    """Handles WebSocket message processing with session-based architecture"""

    def __init__(self, session_manager, username: str):
        self.logger = logging.getLogger(__name__)
        self.session_manager = session_manager
        self.username = username
        self.preview_dir = self._get_preview_dir()

    def _get_preview_dir(self):
        # Define the base directory where previews are stored
        base_preview_dir = Path(settings.BLENDER_RENDER_PREVIEW_DIRECTORY)

        # Create a user-specific directory dynamically
        user_preview_dir = base_preview_dir / self.username / "preview"

        # Ensure the directory exists
        user_preview_dir.mkdir(exist_ok=True, parents=True)

        return user_preview_dir

    async def handle_message(self, username: str, data: Dict[str, Any], client_type: str):
        """
        Process incoming WebSocket messages with proper routing
        """
        try:
            command = data.get("command")
            action = data.get("action")
            status = data.get("status")

            if status == "Connected":
                self.logger.info(f"Client {username} connected")
                session = self.session_manager.get_session(username)
                if session and session.browser_socket:
                    retry_delay = min(
                        session.base_retry_delay * (2 ** session.connection_attempts), 60)
                    await session.browser_socket.send_json({
                        "status": "ACK",
                        "message": "Connection acknowledged",
                        "connectionAttempts": session.connection_attempts,
                        "maxAttempts": session.max_connection_attempts,
                        "retryDelay": retry_delay,
                        "shouldRetry": session.connection_attempts < session.max_connection_attempts
                    })
                return

            # Command completion handler
            if status == "completed":
                await self._handle_command_completion(username, data)
                return

            handlers = {
                "start_preview_rendering": self._handle_preview_rendering,
                "stop_broadcast": self._handle_stop_broadcast,
                "start_broadcast": self._handle_start_broadcast,
                "generate_video": self._handle_generate_video,
                "get_template_controls": self._handle_get_template_controls,
                "template_controls": self._handle_template_controls_response
            }

            handler = handlers.get(command)  # Try command first
            if not handler:
                # Fall back to action if no command handler
                handler = handlers.get(action)

            if handler:
                await handler(username, data, client_type)
            else:
                self.logger.warning(f"Unhandled message: {data}")

        except Exception as e:
            self.logger.error(f"Message processing error: {str(e)}")
            session = self.session_manager.get_session(username)
            if session:
                target_socket = session.browser_socket if client_type == "blender" else session.blender_socket
                if target_socket:
                    await target_socket.send_json({
                        "status": "ERROR",
                        "message": f"Message processing error: {str(e)}"
                    })

    async def _handle_preview_rendering(self, username: str, data: Dict[str, Any], client_type: str):
        """Handle preview rendering requests"""
        if client_type != "browser":
            return

        message_id = str(uuid.uuid4())
        session = self.session_manager.get_session(username)
        self.session_manager.add_pending_request(username, message_id)
        if not session or not session.blender_socket:
            await self._send_error(username, "Blender client not connected")
            return

        command = {
            "command": data.get("command"),
            "params": data.get("params"),
            "message_id": message_id
        }

        await session.blender_socket.send_json(command)
        await session.browser_socket.send_json({
            "status": "OK",
            "message": "Preview rendering started"
        })

    async def _handle_generate_video(self, username: str, data: Dict[str, Any], client_type: str):
        """Handle video generation requests"""
        if client_type != "browser":
            return

        session = self.session_manager.get_session(username)
        if not session or not session.blender_socket:
            await self._send_error(username, "Blender client not connected")
            return

        await session.blender_socket.send_json(data)
        await session.browser_socket.send_json({
            "status": "OK",
            "message": "Video generation started"
        })

    async def _handle_start_broadcast(self, username: str, data: Dict[str, Any], client_type: str):
        """Start/resume frame broadcasting from the last frame or the beginning"""
        session = self.session_manager.get_session(username)
        if not session:
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

    async def _handle_stop_broadcast(self, username: str, data: Dict[str, Any], client_type: str):
        """Stop frame broadcasting immediately"""
        session = self.session_manager.get_session(username)
        if not session:
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

    async def _broadcast_frames(self, username: str):
        """Broadcast frames once (stops after last frame)"""
        session = self.session_manager.get_session(username)
        if not session or not session.browser_socket:
            return

        try:
            frames = sorted(self.preview_dir.glob("frame_*.png"))
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

    async def _handle_get_template_controls(self, username: str, data: Dict[str, Any], client_type: str):
        """Handle template controls request with proper message tracking"""
        try:
            # Generate and track message ID
            message_id = str(uuid.uuid4())
            print(f"Generated new message_id: {message_id}")
            self.session_manager.add_pending_request(username, message_id)

            # Get session and validate connection
            session = self.session_manager.get_session(username)
            if not session or not session.blender_socket:
                await self._send_error(username, "Blender client not connected")
                return

            # Prepare and send command to Blender
            command = {
                "command": "rescan_template",
                "message_id": message_id
            }
            await session.blender_socket.send_json(command)

            # Log successful request
            self.logger.info(
                f"Sent template controls request to Blender for {username} (message_id: {message_id})")

        except Exception as e:
            self.logger.error(
                f"Error handling template controls request: {str(e)}")
            if 'message_id' in locals():
                # Clean up pending request on error
                self.session_manager.remove_pending_request(message_id)
            await self._send_error(username, f"Failed to process template controls request: {str(e)}")

    async def _handle_template_controls_response(self, username: str, data: Dict[str, Any], client_type: str):
        """Handle template controls response"""
        self.logger.debug(
            f"Received template controls response from {username}: {data}")

        try:
            # Verify and extract the response data
            if not isinstance(data, dict):
                self.logger.error(f"Invalid data format: {type(data)}")
                return

            # Extract data from response
            response_data = data.get("data", {})
            if not response_data:
                self.logger.error("No data in template controls response")
                self.logger.debug(f"Response data: {data}")
                return

            # Log the structure of response_data for debugging
            self.logger.debug(f"Response data structure: {response_data}")

            # Extract inner data from response_data
            inner_data = response_data.get("data", {})
            if not inner_data:
                self.logger.error(
                    "No inner data in template controls response")
                self.logger.debug(f"Response data: {response_data}")
                return

            # Log the structure of inner_data for debugging
            self.logger.debug(f"Inner data structure: {inner_data}")

            # Get message_id from inner data
            message_id = inner_data.get("message_id")
            if not message_id:
                self.logger.error(
                    "No message_id in template controls response data")
                self.logger.debug(f"Inner data: {inner_data}")
                return

            # Extract controllables from the inner data object
            controllables = inner_data.get("controllables", {})
            print(
                f"Found message_id: {message_id}, controllables: {bool(controllables)}")

            # Rest of the code remains unchanged...
            self.logger.debug(
                f"Processing response with message_id: {message_id}")
            request_username = self.session_manager.get_pending_request(
                message_id)
            if not request_username:
                self.logger.error(
                    f"No pending request for message_id {message_id}")
                return

            self.logger.debug(
                f"Processing template controls for {request_username}")

            # Get the session for the requesting user
            session = self.session_manager.get_session(request_username)
            if not session:
                self.logger.error(f"No session found for {request_username}")
                return

            if not session.browser_socket:
                self.logger.error(f"No browser socket for {request_username}")
                return

            # Validate controllables data
            if not isinstance(controllables, dict):
                self.logger.error(
                    f"Invalid controllables format: {type(controllables)}")
                controllables = {}

            # Prepare and send the response
            response = {
                "command": "template_controls",
                "controllables": controllables,
                "status": "success",
                "message_id": message_id
            }

            self.logger.debug(
                f"Sending template controls to {request_username}: {response}")
            await session.browser_socket.send_json(response)
            self.logger.info(
                f"Successfully sent template controls to {request_username}")

            # Clean up the pending request after successful response
            self.session_manager.remove_pending_request(message_id)

        except Exception as e:
            self.logger.error(
                f"Error in template controls response handling: {str(e)}")
            # Attempt to send error response if possible
            if 'session' in locals() and session and session.browser_socket:
                await session.browser_socket.send_json({
                    "command": "template_controls",
                    "status": "error",
                    "message": str(e)
                })
            # Don't clean up pending request on error to allow for retries
            if 'message_id' in locals():
                self.logger.debug(
                    f"Keeping pending request for retry. message_id: {message_id}")

    async def _handle_command_completion(self, username: str, data: Dict[str, Any]):
        """Handle command completion"""
        session = self.session_manager.get_session(username)
        if not session or not session.browser_socket:
            return

        await session.browser_socket.send_json({
            "type": "command_completed",
            "command": data.get("command", "unknown"),
            "message_id": data.get("message_id"),
            "status": "success"
        })

    async def _send_error(self, username: str, message: str):
        """Send error message to browser client"""
        session = self.session_manager.get_session(username)
        if session and session.browser_socket:
            await session.browser_socket.send_json({
                "status": "ERROR",
                "message": message
            })
