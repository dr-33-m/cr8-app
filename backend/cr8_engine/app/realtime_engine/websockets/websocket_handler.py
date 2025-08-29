"""
WebSocket handler implementation for cr8_engine with B.L.A.Z.E Agent integration.
This module routes all user messages through the B.L.A.Z.E intelligent agent with dynamic addon capabilities.
"""

import logging
from typing import Dict, Any
from fastapi import WebSocket

# Import B.L.A.Z.E Agent
from app.blaze.agent import BlazeAgent

# Configure logging
logger = logging.getLogger(__name__)


class WebSocketHandler:
    """WebSocket handler powered by B.L.A.Z.E Agent for intelligent scene control."""

    def __init__(self, session_manager, username: str):
        """
        Initialize the WebSocket handler with B.L.A.Z.E Agent.

        Args:
            session_manager: The session manager instance
            username: The username for this handler
        """
        self.session_manager = session_manager
        self.username = username
        self.logger = logging.getLogger(__name__)

        # Get or create session-specific B.L.A.Z.E Agent
        session = session_manager.get_session(username)
        if session and session.blaze_agent is None:
            # Create B.L.A.Z.E Agent with pure dynamic toolset (no legacy handlers)
            # The agent will get its capabilities from dynamically discovered addons
            session.blaze_agent = BlazeAgent(session_manager, handlers=None)
            self.logger.info(
                f"Created new B.L.A.Z.E Agent for session {username} with dynamic capabilities")

        # Use session's agent
        self.blaze_agent = session.blaze_agent if session else None

        # Initialize logger
        logger.info(
            f"WebSocket Handler with B.L.A.Z.E initialized for user {username}")

    async def handle_message(self, username: str, data: Dict[str, Any], client_type: str):
        """
        Process incoming WebSocket messages through B.L.A.Z.E Agent.

        Args:
            username: The username of the client
            data: The message data
            client_type: The type of client (browser or blender)
        """
        try:
            message_type = data.get("type")
            command = data.get("command")
            status = data.get("status")

            # Handle system messages (connection, browser_ready, etc.)
            if data.get("type") == "system" or command in ["browser_ready", "connection_status"]:
                await self._handle_system_message(username, data, client_type)
                return

            # Handle template controls updates (needed for B.L.A.Z.E context)
            if command == 'get_template_controls' or (command and 'template' in command and '_result' in command):
                await self._handle_template_message(username, data, client_type)
                return

            # Handle Blender responses that need to be processed
            if client_type == "blender" and ((command and '_result' in command) or data.get("type") == "registry_updated"):
                await self._handle_blender_response(username, data)
                return

            # Route user messages to B.L.A.Z.E Agent
            if client_type == "browser" and data.get("message"):
                await self._route_to_blaze(username, data, client_type)
                return

            # Forward other messages (primarily Blender communication)
            await self._forward_message(username, data, client_type)

        except Exception as e:
            self.logger.error(f"Message processing error: {str(e)}")
            await self._send_error(username, f"Message processing error: {str(e)}")

    async def _handle_system_message(self, username: str, data: Dict[str, Any], client_type: str):
        """Handle system messages (connection, browser_ready, etc.)"""
        command = data.get("command")
        status = data.get("status")

        # Handle connection status
        if status and status.lower() == "connected" or command == "connection_status":
            self.logger.info(
                f"Client {username} connected with status: {status}")
            session = self.session_manager.get_session(username)
            if session and session.browser_socket:
                retry_delay = min(session.base_retry_delay *
                                  (2 ** session.connection_attempts), 60)
                await session.browser_socket.send_json({
                    "status": "ACK",
                    "message": "Connection acknowledged",
                    "connectionAttempts": session.connection_attempts,
                    "maxAttempts": session.max_connection_attempts,
                    "retryDelay": retry_delay,
                    "shouldRetry": session.connection_attempts < session.max_connection_attempts
                })
            return

        # Handle browser ready signal
        if command == "browser_ready" and client_type == "browser":
            try:
                recovery_mode = data.get("recovery", False)
                if recovery_mode:
                    session = self.session_manager.get_session(username)
                    if session and session.state != "waiting_for_browser_ready":
                        session.state = "waiting_for_browser_ready"
                        self.logger.info(
                            f"Resetting session state for {username} in recovery mode")

                await self.session_manager.launch_blender_for_session(username)
                session = self.session_manager.get_session(username)
                if session and session.browser_socket:
                    await session.browser_socket.send_json({
                        "type": "system",
                        "status": "launching_blender",
                        "message": "Launching Blender instance"
                    })
                self.logger.info(
                    f"Browser ready signal received from {username}, launching Blender")
            except ValueError as e:
                self.logger.error(f"Error launching Blender: {str(e)}")
                session = self.session_manager.get_session(username)
                if session and session.browser_socket:
                    await session.browser_socket.send_json({
                        "type": "system",
                        "status": "error",
                        "message": f"Failed to launch Blender: {str(e)}"
                    })
            return

    async def _handle_template_message(self, username: str, data: Dict[str, Any], client_type: str):
        """Handle template control messages and update B.L.A.Z.E context"""
        command = data.get("command")

        if command == 'get_template_controls':
            # Forward to Blender
            await self.session_manager.forward_message(username, data, "blender")
        elif command and 'template' in command and '_result' in command:
            # Update B.L.A.Z.E context with template controls
            controls = data.get("data", {}).get("controls", [])
            self.logger.info(
                f"Received template controls for {username}: {len(controls)} controls")

            if controls and isinstance(controls, list):
                # Parse the list of controls and categorize by type
                template_controls = {
                    "cameras": [c for c in controls if c.get("type") == "camera"],
                    "lights": [c for c in controls if c.get("type") == "light"],
                    "materials": [c for c in controls if c.get("type") == "material"],
                    "objects": [c for c in controls if c.get("type") == "object"]
                }

                self.logger.info(
                    f"Categorized controls - Cameras: {len(template_controls['cameras'])}, Lights: {len(template_controls['lights'])}")

                self.blaze_agent.update_scene_context(
                    username, template_controls)
            else:
                self.logger.warning(f"No valid controls found for {username}")

            # Forward response to browser
            await self.session_manager.forward_message(username, data, "browser")

    async def _handle_blender_response(self, username: str, data: Dict[str, Any]):
        """Handle responses from Blender and forward to browser"""

        # Check for registry update events
        if data.get("type") == "registry_updated":
            self.logger.info(
                f"Detected registry update message from Blender for {username}")
            await self._handle_registry_update(username, data)
            # Don't forward registry updates to browser - these are internal
            return

        # Forward most Blender responses to browser
        await self.session_manager.forward_message(username, data, "browser")

    async def _handle_registry_update(self, username: str, data: Dict[str, Any]):
        """Handle registry update events from Blender AI Router"""
        try:
            self.logger.info(
                f"Received registry update from Blender for user {username}")

            # Update B.L.A.Z.E agent with new capabilities
            self.blaze_agent.handle_registry_update(data)

            # Send acknowledgment back to Blender (optional)
            session = self.session_manager.get_session(username)
            if session and session.blender_socket:
                ack_message = {
                    "type": "registry_update_ack",
                    "status": "processed",
                    "message": "Registry update processed successfully"
                }
                await session.blender_socket.send_json(ack_message)

        except Exception as e:
            self.logger.error(f"Error handling registry update: {str(e)}")

            # Send error acknowledgment
            session = self.session_manager.get_session(username)
            if session and session.blender_socket:
                error_message = {
                    "type": "registry_update_ack",
                    "status": "error",
                    "message": f"Failed to process registry update: {str(e)}"
                }
                await session.blender_socket.send_json(error_message)

    async def _route_to_blaze(self, username: str, data: Dict[str, Any], client_type: str):
        """Route user messages to B.L.A.Z.E Agent"""
        try:
            message = data.get("message", "")
            if not message:
                await self._send_error(username, "No message provided")
                return

            # Process message with B.L.A.Z.E Agent
            response = await self.blaze_agent.process_message(username, message, client_type)

            # Send response back to browser
            session = self.session_manager.get_session(username)
            if session and session.browser_socket:
                await session.browser_socket.send_json(response)

        except Exception as e:
            self.logger.error(f"Error routing to B.L.A.Z.E: {str(e)}")
            await self._send_error(username, f"B.L.A.Z.E processing error: {str(e)}")

    async def _forward_message(self, username: str, data: Dict[str, Any], client_type: str):
        """Forward message to the other client type"""
        target = "blender" if client_type == "browser" else "browser"
        await self.session_manager.forward_message(username, data, target)
        self.logger.info(f"Forwarded message from {client_type} to {target}")

    async def _send_error(self, username: str, message: str):
        """Send error message to browser client"""
        session = self.session_manager.get_session(username)
        if session and session.browser_socket:
            await session.browser_socket.send_json({
                "type": "agent_response",
                "status": "error",
                "message": message
            })
