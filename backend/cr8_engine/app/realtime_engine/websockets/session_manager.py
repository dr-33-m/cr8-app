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
        self.pending_requests: Dict[str, str] = {}  # message_id -> username
        self.last_connection_attempt = 0  # timestamp of last connection attempt
        self.connection_attempts = 0  # number of connection attempts
        # maximum number of connection attempts before giving up
        self.max_connection_attempts = 5
        self.base_retry_delay = 1  # base delay in seconds between retries


class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self.logger = logging.getLogger(__name__)

    async def create_browser_session(self, username: str, websocket: WebSocket, blend_file: str) -> Session:
        """Create a new session for a browser client"""
        try:
            current_time = asyncio.get_event_loop().time()

            if username in self.sessions:
                session = self.sessions[username]
                if session.is_active:
                    if session.state == SessionState.CONNECTED:
                        # Update the browser socket
                        session.browser_socket = websocket
                        return session
                    else:
                        # Check if we should allow a new connection attempt
                        time_since_last_attempt = current_time - session.last_connection_attempt
                        retry_delay = min(
                            session.base_retry_delay * (2 ** session.connection_attempts), 60)

                        if time_since_last_attempt < retry_delay:
                            raise ValueError(
                                f"Please wait {int(retry_delay - time_since_last_attempt)} seconds before reconnecting")

                        if session.connection_attempts >= session.max_connection_attempts:
                            raise ValueError(
                                "Maximum connection attempts exceeded. Please try again later")

                        # Clean up partial session and allow retry
                        await self.cleanup_session(username)

            # Create new session with updated connection tracking
            session = Session(username, browser_socket=websocket)
            session.last_connection_attempt = current_time
            session.connection_attempts = 0 if not username in self.sessions else self.sessions[
                username].connection_attempts + 1
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
                session.last_connection_attempt = asyncio.get_event_loop().time()
                session.connection_attempts += 1

                # Calculate retry delay with exponential backoff
                retry_delay = min(session.base_retry_delay *
                                  (2 ** session.connection_attempts), 60)

                # If we've exceeded max attempts, clean up immediately
                if session.connection_attempts >= session.max_connection_attempts:
                    await self.cleanup_session(username)
                    return

                # Otherwise wait briefly before cleanup to allow reconnection
                await asyncio.sleep(retry_delay)
                if username in self.sessions and not session.browser_socket:
                    await self.cleanup_session(username)
            else:  # blender
                session.blender_socket = None
                session.state = SessionState.DISCONNECTED

                # Reset connection attempts when Blender disconnects
                session.connection_attempts = 0

                # Notify browser if it's still connected
                if session.browser_socket:
                    try:
                        await session.browser_socket.send_json({
                            "type": "system",
                            "status": "blender_disconnected",
                            "message": "Blender instance disconnected. Attempting to reconnect...",
                            "shouldReconnect": True
                        })
                    except Exception as e:
                        self.logger.error(
                            f"Error notifying browser of Blender disconnect: {str(e)}")

                # Don't immediately clean up - give time for reconnection
                await asyncio.sleep(5)
                if username in self.sessions and not session.blender_socket:
                    await self.cleanup_session(username)

    def get_session(self, username: str) -> Optional[Session]:
        """Get a session by username"""
        return self.sessions.get(username)

    def add_pending_request(self, username: str, message_id: str) -> None:
        """Add a pending request to the user's session"""
        session = self.sessions.get(username)
        if session:
            session.pending_requests[message_id] = username
            self.logger.debug(
                f"Added pending request {message_id} for {username}")

    def get_pending_request(self, message_id: str) -> Optional[str]:
        """Get the username associated with a pending request"""
        for session in self.sessions.values():
            if message_id in session.pending_requests:
                return session.pending_requests[message_id]
        return None

    def remove_pending_request(self, message_id: str) -> None:
        """Remove a pending request from its session"""
        for session in self.sessions.values():
            if message_id in session.pending_requests:
                del session.pending_requests[message_id]
                self.logger.debug(f"Removed pending request {message_id}")
                break
