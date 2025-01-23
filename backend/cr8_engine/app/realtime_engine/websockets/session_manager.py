# app/websockets/session_manager.py
from typing import Dict, Optional
import asyncio
import logging
from fastapi import WebSocket, WebSocketDisconnect
from app.services.blender_service import BlenderService


class SessionState:
    WAITING_FOR_BLENDER = "waiting_for_blender"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"


class Session:
    def __init__(self, username: str, browser_socket: Optional[WebSocket] = None):
        self.username = username
        self.browser_socket = browser_socket
        self.blender_socket = None
        self.is_active = True
        self.state = SessionState.DISCONNECTED
        self.connection_timeout = 30  # seconds to wait for Blender to connect
        self.should_broadcast = False
        self.last_frame_index = -1


class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self.logger = logging.getLogger(__name__)

    async def create_browser_session(self, username: str, websocket: WebSocket, blend_file: str) -> Session:
        """Create a new session for a browser client"""
        try:
            if username in self.sessions:
                session = self.sessions[username]
                if session.is_active:
                    if session.state == SessionState.CONNECTED:
                        # Instead of raising an error, update the browser socket
                        session.browser_socket = websocket
                        return session
                    else:
                        # Clean up partial session
                        await self.cleanup_session(username)

            # Create new session
            session = Session(username, browser_socket=websocket)
            self.sessions[username] = session

            # Launch Blender instance using the service
            success = await BlenderService.launch_instance(username, blend_file)
            if not success:
                await self.cleanup_session(username)
                raise ValueError("Failed to launch Blender instance")

            # Set state to waiting for Blender connection
            session.state = SessionState.WAITING_FOR_BLENDER

            # Start timeout monitor for Blender connection
            asyncio.create_task(self._monitor_blender_connection(username))

            return session

        except Exception as e:
            self.logger.error(
                f"Error creating browser session for {username}: {str(e)}")
            raise

    async def register_blender(self, username: str, websocket: WebSocket) -> None:
        """Register a Blender client to an existing session"""
        if username not in self.sessions:
            raise ValueError(f"No browser session found for {username}")

        session = self.sessions[username]

        # Check if we're waiting for this Blender connection
        if session.state != SessionState.WAITING_FOR_BLENDER:
            raise ValueError(f"Unexpected Blender connection for {username}")

        # Register the Blender socket
        session.blender_socket = websocket
        session.state = SessionState.CONNECTED

        # Notify browser client that Blender is connected
        if session.browser_socket:
            try:
                await session.browser_socket.send_json({
                    "type": "system",
                    "status": "blender_connected",
                    "message": "Blender instance connected successfully"
                })
            except Exception as e:
                self.logger.error(
                    f"Error notifying browser of Blender connection: {str(e)}")

        self.logger.info(f"Blender client registered for session {username}")

    async def _monitor_blender_connection(self, username: str):
        """Monitor for successful Blender connection within timeout period"""
        session = self.sessions.get(username)
        if not session:
            return

        try:
            start_time = asyncio.get_event_loop().time()
            while (asyncio.get_event_loop().time() - start_time) < session.connection_timeout:
                if session.state == SessionState.CONNECTED:
                    # Blender connected successfully
                    return
                elif not session.is_active:
                    # Session was cleaned up
                    return
                await asyncio.sleep(1)

            # If we get here, timeout occurred
            if session.state == SessionState.WAITING_FOR_BLENDER:
                self.logger.error(f"Blender connection timeout for {username}")
                # Notify browser client
                if session.browser_socket:
                    try:
                        await session.browser_socket.send_json({
                            "type": "system",
                            "status": "error",
                            "message": "Blender connection timeout"
                        })
                    except Exception as e:
                        self.logger.error(
                            f"Error sending timeout notification: {str(e)}")
                # Clean up the session
                await self.cleanup_session(username)

        except Exception as e:
            self.logger.error(f"Error monitoring Blender connection: {str(e)}")

    async def cleanup_session(self, username: str):
        """Clean up a session and its associated resources"""
        if username in self.sessions:
            session = self.sessions[username]
            session.is_active = False

            # Close WebSocket connections
            if session.browser_socket:
                try:
                    await session.browser_socket.send_json({
                        "type": "system",
                        "status": "session_closed",
                        "message": "Session terminated"
                    })
                    await session.browser_socket.close()
                except Exception as e:
                    self.logger.error(
                        f"Error closing browser socket: {str(e)}")

            if session.blender_socket:
                try:
                    await session.blender_socket.close()
                except Exception as e:
                    self.logger.error(
                        f"Error closing blender socket: {str(e)}")

            # Terminate Blender instance
            await BlenderService.terminate_instance(username)

            # Remove session
            del self.sessions[username]
            self.logger.info(f"Cleaned up session for {username}")

    async def forward_message(self, from_username: str, message: dict, target: str = "blender"):
        """Forward message between browser and blender clients"""
        if from_username not in self.sessions:
            raise ValueError(f"No session found for {from_username}")

        session = self.sessions[from_username]
        if session.state != SessionState.CONNECTED:
            raise ValueError(
                f"Session not fully connected for {from_username}")

        target_socket = session.blender_socket if target == "blender" else session.browser_socket

        if target_socket:
            await target_socket.send_json(message)
        else:
            self.logger.warning(
                f"No {target} socket found for {from_username}")

    async def handle_disconnect(self, username: str, client_type: str):
        """Handle client disconnection"""
        if username in self.sessions:
            session = self.sessions[username]

            if client_type == "browser":
                session.browser_socket = None

                await asyncio.sleep(5)
                if username in self.sessions and not session.browser_socket:
                    # Only cleanup if no new browser connection was established
                    await self.cleanup_session(username)
            else:  # blender
                session.blender_socket = None
                session.state = SessionState.DISCONNECTED
                # Notify browser if it's still connected
                if session.browser_socket:
                    try:
                        await session.browser_socket.send_json({
                            "type": "system",
                            "status": "blender_disconnected",
                            "message": "Blender instance disconnected"
                        })
                    except Exception as e:
                        self.logger.error(
                            f"Error notifying browser of Blender disconnect: {str(e)}")
                # Clean up the session
                await self.cleanup_session(username)

    def get_session(self, username: str) -> Optional[Session]:
        """Get a session by username"""
        return self.sessions.get(username)
