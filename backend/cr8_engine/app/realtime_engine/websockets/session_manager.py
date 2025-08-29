# app/websockets/session_manager.py
from typing import Dict, Optional
import asyncio
import logging
import uuid
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
        self.pending_template_requests = []  # Queued template control requests
        self.last_connection_attempt = 0  # timestamp of last connection attempt
        self.connection_attempts = 0  # number of connection attempts
        # maximum number of connection attempts before giving up
        self.max_connection_attempts = 5
        self.base_retry_delay = 1  # base delay in seconds between retries
        # Track socket states
        self.browser_socket_closed = False
        self.blender_socket_closed = False
        # Single B.L.A.Z.E agent instance per session
        self.blaze_agent = None


class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self.logger = logging.getLogger(__name__)

    async def create_browser_session(self, username: str, websocket: WebSocket, blend_file_path: str) -> Session:
        """Create a new session for a browser client"""
        try:
            current_time = asyncio.get_event_loop().time()

            # Check if we already have a session for this user
            if username in self.sessions:
                session = self.sessions[username]
                if session.is_active:
                    # Update browser socket regardless
                    old_socket = session.browser_socket
                    session.browser_socket = websocket
                    session.browser_socket_closed = False
                    self.logger.info(
                        f"Updated browser socket for {username} (refresh detected)")

                    # Check if Blender is actually running
                    blender_running = await BlenderService.check_instance_status(username)
                    blender_socket_alive = session.blender_socket and not session.blender_socket_closed

                    if blender_running:
                        if session.state == SessionState.CONNECTED and blender_socket_alive:
                            # Best case: Blender is running and connected - just notify browser
                            await websocket.send_json({
                                "type": "system",
                                "status": "blender_connected",
                                "message": "Reconnected to existing Blender instance"
                            })
                            self.logger.info(
                                f"Browser reconnected to existing Blender for {username}")
                            return session
                        elif session.state == SessionState.WAITING_FOR_BLENDER:
                            # Blender is running but not connected to WS - wait for reconnect
                            await websocket.send_json({
                                "type": "system",
                                "status": "waiting_for_blender",
                                "message": "Waiting for Blender to reconnect..."
                            })
                            self.logger.info(
                                f"Waiting for Blender WS reconnection for {username}")
                            return session
                        else:
                            # Blender is running but in unexpected state - reset to allow browser_ready
                            session.state = "waiting_for_browser_ready"
                            session.blend_file = blend_file_path
                            self.logger.info(
                                f"Blender running but in state {session.state} for {username}, resetting")
                            return session
                    else:
                        # Blender is not running but session exists - reset to allow new launch
                        session.state = "waiting_for_browser_ready"
                        session.blend_file = blend_file_path
                        session.blender_socket = None
                        session.blender_socket_closed = True
                        self.logger.info(
                            f"Resetting session for {username} - Blender not running")
                        return session

                    # Original reconnection logic for non-refresh cases
                    if session.state == SessionState.CONNECTED:
                        return session
                    else:
                        # Check if we should allow a new connection attempt
                        time_since_last_attempt = current_time - session.last_connection_attempt
                        retry_delay = min(
                            session.base_retry_delay * (2 ** session.connection_attempts), 60)

                        # Calculate wait time with a minimum of 1 second to avoid "0 seconds" message
                        wait_time = max(
                            1, int(retry_delay - time_since_last_attempt))

                        # Only enforce delay if it's significant (more than 1 second)
                        if time_since_last_attempt < retry_delay and wait_time > 1:
                            raise ValueError(
                                f"Please wait {wait_time} seconds before reconnecting")

                        if session.connection_attempts >= session.max_connection_attempts:
                            raise ValueError(
                                "Maximum connection attempts exceeded. Please try again later")

                        # Clean up partial session and allow retry
                        await self.cleanup_session(username)

            # Create new session with updated connection tracking
            session = Session(username, browser_socket=websocket)
            session.last_connection_attempt = current_time
            # Store blend_file for later use when launching Blender
            session.blend_file = blend_file_path

            # Reset connection attempts for new sessions or increment for retries
            if not username in self.sessions:
                session.connection_attempts = 0
            else:
                # Only increment if the previous session wasn't fully connected
                prev_session = self.sessions[username]
                if prev_session.state != SessionState.CONNECTED:
                    session.connection_attempts = prev_session.connection_attempts + 1
                else:
                    # If previous session was fully connected, reset counter
                    session.connection_attempts = 0

            self.sessions[username] = session

            # Set state to waiting for browser ready signal instead of launching Blender immediately
            session.state = "waiting_for_browser_ready"

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

        # Verify connection is still open with a proper command ping and wait for response
        try:
            ping_message_id = str(uuid.uuid4())
            await websocket.send_json({
                "command": "ping",
                "message_id": ping_message_id
            })

            # Create a future to wait for the ping response
            ping_response_future = asyncio.Future()

            # Define a response handler
            async def receive_ping_response():
                try:
                    # Wait for the ping response with a timeout
                    response_data = await asyncio.wait_for(websocket.receive_json(), timeout=5.0)

                    # Check if this is the ping response we're waiting for
                    if (response_data.get("command") == "ping_result" and
                        response_data.get("status") == "success" and
                            response_data.get("data", {}).get("pong") == True):
                        ping_response_future.set_result(True)
                    else:
                        # Handle other messages that might come in first
                        self.logger.debug(
                            f"Received non-ping response during verification: {response_data}")
                        # Recursively wait for the next message
                        await receive_ping_response()
                except asyncio.TimeoutError:
                    ping_response_future.set_exception(
                        ValueError("Ping response timeout"))
                except Exception as e:
                    ping_response_future.set_exception(e)

            # Start listening for the response
            asyncio.create_task(receive_ping_response())

            # Wait for the ping response
            await ping_response_future
            self.logger.info(f"Ping verification successful for {username}")

        except Exception as e:
            self.logger.error(
                f"Blender connection verification failed: {str(e)}")
            raise ValueError(f"Blender connection unstable: {str(e)}")

        # Register the Blender socket
        session.blender_socket = websocket
        session.blender_socket_closed = False
        session.state = SessionState.CONNECTED

        # Reset connection attempts counter on successful connection
        session.connection_attempts = 0

        # Notify browser client that Blender is connected
        if session.browser_socket and not session.browser_socket_closed:
            try:
                await session.browser_socket.send_json({
                    "type": "system",
                    "status": "blender_connected",
                    "message": "Blender instance connected successfully"
                })
            except Exception as e:
                session.browser_socket_closed = True
                self.logger.error(
                    f"Error notifying browser of Blender connection: {str(e)}")

        # Process any queued template control requests
        if session.pending_template_requests:
            self.logger.info(
                f"Processing {len(session.pending_template_requests)} queued template requests")
            from app.realtime_engine.websockets.websocket_handler import WebSocketHandler
            handler = WebSocketHandler(self, username)

            for request in session.pending_template_requests:
                try:
                    await handler.handle_message(username, {"command": "get_template_controls"}, "browser")
                except Exception as e:
                    self.logger.error(
                        f"Error processing queued template request: {str(e)}")

            # Clear the queue
            session.pending_template_requests = []

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
            if session.browser_socket and not session.browser_socket_closed:
                try:
                    # Only try to send if socket appears to be open
                    try:
                        await session.browser_socket.send_json({
                            "type": "system",
                            "status": "session_closed",
                            "message": "Session terminated"
                        })
                    except Exception:
                        # If send fails, just log and continue with close
                        self.logger.debug(
                            "Could not send session_closed message")

                    await session.browser_socket.close()
                    session.browser_socket_closed = True
                except Exception as e:
                    self.logger.error(
                        f"Error closing browser socket: {str(e)}")

            if session.blender_socket and not session.blender_socket_closed:
                try:
                    await session.blender_socket.close()
                    session.blender_socket_closed = True
                except Exception as e:
                    self.logger.error(
                        f"Error closing blender socket: {str(e)}")

            # Terminate Blender instance
            try:
                await BlenderService.terminate_instance(username)
            except Exception as e:
                self.logger.error(
                    f"Error terminating Blender instance: {str(e)}")

            # Remove session
            del self.sessions[username]
            self.logger.info(f"Cleaned up session for {username}")

    async def forward_message(self, from_username: str, message: dict, target: str = "blender"):
        """Forward message between browser and blender clients"""
        if from_username not in self.sessions:
            raise ValueError(f"No session found for {from_username}")

        session = self.sessions[from_username]

        # Special handling for template control requests when Blender is not connected
        if message.get("command") == "get_template_controls" and (
            session.state != SessionState.CONNECTED or
            not session.blender_socket or
            session.blender_socket_closed
        ):
            # Queue the request for later processing
            self.logger.info(
                f"Queuing template control request for {from_username}")
            session.pending_template_requests.append(message)

            # Notify browser that request is queued
            if session.browser_socket and not session.browser_socket_closed:
                try:
                    await session.browser_socket.send_json({
                        "type": "system",
                        "status": "waiting_for_blender",
                        "message": "Template controls request queued until Blender connects"
                    })
                except Exception as e:
                    session.browser_socket_closed = True
                    self.logger.error(
                        f"Error sending queue notification: {str(e)}")

            return

        if session.state != SessionState.CONNECTED:
            raise ValueError(
                f"Session not fully connected for {from_username}")

        target_socket = session.blender_socket if target == "blender" else session.browser_socket
        socket_closed = session.blender_socket_closed if target == "blender" else session.browser_socket_closed

        if target_socket and not socket_closed:
            try:
                await target_socket.send_json(message)
            except Exception as e:
                # Mark socket as closed if send fails
                if target == "blender":
                    session.blender_socket_closed = True
                else:
                    session.browser_socket_closed = True
                self.logger.error(
                    f"Error forwarding message to {target}: {str(e)}")
                raise ValueError(
                    f"Failed to forward message to {target}: {str(e)}")
        else:
            self.logger.warning(
                f"No {target} socket found for {from_username} or socket is closed")

    async def handle_disconnect(self, username: str, client_type: str):
        """Handle client disconnection"""
        if username in self.sessions:
            session = self.sessions[username]

            if client_type == "browser":
                session.browser_socket = None
                session.browser_socket_closed = True
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
                if username in self.sessions and (not session.browser_socket or session.browser_socket_closed):
                    await self.cleanup_session(username)
            else:  # blender
                session.blender_socket = None
                session.blender_socket_closed = True
                session.state = SessionState.DISCONNECTED

                # Reset connection attempts when Blender disconnects
                session.connection_attempts = 0

                # Notify browser if it's still connected
                if session.browser_socket and not session.browser_socket_closed:
                    try:
                        await session.browser_socket.send_json({
                            "type": "system",
                            "status": "blender_disconnected",
                            "message": "Blender instance disconnected. Attempting to reconnect...",
                            "shouldReconnect": True
                        })
                    except Exception as e:
                        session.browser_socket_closed = True
                        self.logger.error(
                            f"Error notifying browser of Blender disconnect: {str(e)}")

                # Don't immediately clean up - give time for reconnection
                await asyncio.sleep(5)
                if username in self.sessions and (not session.blender_socket or session.blender_socket_closed):
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

    async def launch_blender_for_session(self, username: str):
        """Launch Blender for a session that's ready"""
        session = self.get_session(username)
        if not session:
            raise ValueError(f"No session found for {username}")

        if session.state != "waiting_for_browser_ready":
            raise ValueError(
                f"Session for {username} is not waiting for browser ready signal")

        # Launch Blender instance using the service
        success = await BlenderService.launch_instance(username, session.blend_file)
        if not success:
            await self.cleanup_session(username)
            raise ValueError("Failed to launch Blender instance")

        # Set state to waiting for Blender connection
        session.state = SessionState.WAITING_FOR_BLENDER

        # Start timeout monitor for Blender connection
        asyncio.create_task(self._monitor_blender_connection(username))

        self.logger.info(
            f"Launched Blender instance for {username} with file {session.blend_file}")

    def remove_pending_request(self, message_id: str) -> None:
        """Remove a pending request from its session"""
        for session in self.sessions.values():
            if message_id in session.pending_requests:
                del session.pending_requests[message_id]
                self.logger.debug(f"Removed pending request {message_id}")
                break
