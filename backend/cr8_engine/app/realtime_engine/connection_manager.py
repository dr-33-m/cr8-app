import asyncio
import json
import logging
import base64
from typing import Dict, Any, Optional
from pathlib import Path
from fastapi import WebSocket, WebSocketDisconnect


class WebSocketConnectionManager:
    """Manage WebSocket connections using FastAPI with enhanced error handling and logging."""

    def __init__(self, preview_dir: Optional[Path] = None):
        """
        Initialize the connection manager.

        :param preview_dir: Directory for storing preview frames
        """
        self.logger = logging.getLogger(__name__)
        self.connections: Dict[str, WebSocket] = {}
        self.preview_dir = Path(
            "/media/970_evo/SC Studio/cr8-xyz/Test Renders") / "box_preview"
        self.preview_dir.mkdir(exist_ok=True, parents=True)

        # Create a thread-safe event for frame broadcasting
        self.frame_broadcast_event = asyncio.Event()
        self.stop_broadcast_event = asyncio.Event()
        self.broadcast_task: Optional[asyncio.Task] = None

    async def send_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """
        Send a message to a specific WebSocket client with robust error handling.

        :param websocket: Target WebSocket connection
        :param message: Message to send
        """
        try:
            await websocket.send_json(message)
            self.logger.info(f"Message sent to client: {message}")
        except WebSocketDisconnect:
            self.logger.warning(
                "Cannot send message: Connection to client closed")
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")

    def register_connection(self, client_id: str, websocket: WebSocket):
        """
        Register a new WebSocket connection.

        :param client_id: Unique identifier for the client
        :param websocket: WebSocket connection
        """
        if client_id in self.connections:
            self.logger.warning(
                f"Replacing existing connection for client {client_id}")

        self.connections[client_id] = websocket
        self.logger.info(f"Client {client_id} connected")

    def unregister_connection(self, client_id: str):
        """
        Remove a WebSocket connection.

        :param client_id: Unique identifier for the client
        """
        if client_id in self.connections:
            del self.connections[client_id]
            self.logger.info(f"Client {client_id} disconnected")

    async def broadcast_frame(self):
        """
        Efficiently broadcast frames to browser client with minimal performance overhead.
        Uses asyncio's native cancellation for responsive stopping.
        """
        try:
            while not self.stop_broadcast_event.is_set():
                # Check if broadcast task is cancelled
                if self.broadcast_task.cancelled():
                    break
                # Wait for the frame broadcast event
                await self.frame_broadcast_event.wait()

                # Load and broadcast frames
                frames = sorted(self.preview_dir.glob("frame_*.png"))
                if not frames:
                    self.logger.warning("No frames found to broadcast.")
                    break

                for frame in frames:
                    if self.stop_broadcast_event.is_set():
                        break

                    await self._broadcast_frames(frame)

                # Reset the event so it can be triggered again for subsequent broadcasts
                self.frame_broadcast_event.clear()

        except Exception as e:
            self.logger.error(f"Error in frame broadcasting: {e}")
        finally:
            self.logger.info("Frame broadcasting loop exited.")
            self.frame_broadcast_event.clear()
            self.stop_broadcast_event.clear()

    async def _broadcast_frames(self, frame: Path):
        """
        Internal method to broadcast a single frame to connected browser clients.

        :param frame: Path to the frame image
        """
        browser_socket = self.connections.get('browser')
        if not browser_socket:
            return

        try:
            with open(frame, 'rb') as img_file:
                img_str = base64.b64encode(img_file.read()).decode()

            await self.send_message(browser_socket, {'type': 'frame', 'data': img_str})

        except WebSocketDisconnect:
            # Handle client disconnection gracefully
            self.logger.warning(
                f"Client disconnected while sending frame {frame}")
        except Exception as e:
            self.logger.error(f"Error broadcasting frame {frame}: {e}")
