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

    def __init__(self, session_manager):
        self.logger = logging.getLogger(__name__)
        self.session_manager = session_manager
        self.preview_dir = Path(
            settings.BLENDER_RENDER_PREVIEW_DIRECTORY) / "test_preview"
        self.preview_dir.mkdir(exist_ok=True, parents=True)
        self.pending_requests: Dict[str, str] = {}  # message_id -> username

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
        self.pending_requests[message_id] = username

        session = self.session_manager.get_session(username)
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
        """Start frame broadcasting"""
        session = self.session_manager.get_session(username)
        if not session:
            return

        # Set the flag to start broadcasting
        session.should_broadcast = True

        # Start the broadcasting task if it doesn't exist or has completed
        if not hasattr(session, 'broadcast_task') or session.broadcast_task.done():
            session.broadcast_task = asyncio.create_task(
                self._broadcast_frames(username)
            )

        # Notify the browser client that broadcasting has started
        if session.browser_socket:
            await session.browser_socket.send_json({
                "status": "OK",
                "message": "Frame broadcast started"
            })

    async def _handle_stop_broadcast(self, username: str, data: Dict[str, Any], client_type: str):
        """Stop frame broadcasting"""
        session = self.session_manager.get_session(username)
        if not session:
            return

        # Set the flag to stop broadcasting
        session.should_broadcast = False

        # Cancel the broadcasting task if it exists and is running
        if hasattr(session, 'broadcast_task') and not session.broadcast_task.done():
            session.broadcast_task.cancel()
            try:
                await session.broadcast_task  # Wait for the task to be cancelled
            except asyncio.CancelledError:
                self.logger.info(f"Broadcast task canceled for {username}")

        # Notify the browser client that broadcasting has stopped
        if session.browser_socket:
            await session.browser_socket.send_json({
                "status": "OK",
                "message": "Frame broadcast stopped"
            })

    async def _broadcast_frames(self, username: str):
        """Broadcast frames to browser client with pause/resume support"""
        session = self.session_manager.get_session(username)
        if not session or not session.browser_socket:
            return

        try:
            frames = sorted(self.preview_dir.glob("frame_*.png"))
            if not frames:
                return  # Exit if no frames are available

            # Add tracking for last broadcasted frame index
            if not hasattr(session, 'last_frame_index'):
                session.last_frame_index = -1

            for frame_index, frame in enumerate(frames):
                # Skip frames already broadcasted if resuming
                if frame_index <= session.last_frame_index:
                    continue

                if not session.should_broadcast:  # Stop if flag is False
                    break

                try:
                    with open(frame, 'rb') as img_file:
                        img_str = base64.b64encode(img_file.read()).decode()
                        await session.browser_socket.send_json({
                            'type': 'frame',
                            'data': img_str,
                            'frame_index': frame_index
                        })

                    # Update last broadcasted frame index
                    session.last_frame_index = frame_index

                except Exception as e:
                    self.logger.error(f"Error sending frame: {e}")
                    session.should_broadcast = False
                    return

                # Optional: small delay between frames
                await asyncio.sleep(0.033)  # ~30 FPS

            # Send a final message indicating broadcast is complete
            await session.browser_socket.send_json({
                'type': 'broadcast_complete'
            })

        except asyncio.CancelledError:
            self.logger.info(f"Frame broadcast cancelled for {username}")
        except Exception as e:
            self.logger.error(f"Error in frame broadcasting: {e}")
        finally:
            session.should_broadcast = False  # Reset the flag when broadcasting stops

    async def _handle_get_template_controls(self, username: str, data: Dict[str, Any], client_type: str):
        """Handle template controls request"""
        message_id = str(uuid.uuid4())
        self.pending_requests[message_id] = username

        session = self.session_manager.get_session(username)
        if not session or not session.blender_socket:
            await self._send_error(username, "Blender client not connected")
            return

        command = {
            "command": "rescan_template",
            "message_id": message_id
        }
        await session.blender_socket.send_json(command)

    async def _handle_template_controls_response(self, username: str, data: Dict[str, Any], client_type: str):
        """Handle template controls response"""
        message_id = data.get("data", {}).get("message_id")
        if not message_id:
            self.logger.warning("No message_id in template controls response")
            return

        request_username = self.pending_requests.get(message_id)
        if not request_username:
            self.logger.warning(
                f"No pending request for message_id {message_id}")
            return

        session = self.session_manager.get_session(request_username)
        if session and session.browser_socket:
            response = {
                "command": "template_controls",
                "controllables": data["data"]["controllables"]
            }
            await session.browser_socket.send_json(response)
            self.logger.info(f"Sent template controls to {request_username}")
        else:
            self.logger.warning(
                f"No session or browser socket for {request_username}")

        del self.pending_requests[message_id]

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
