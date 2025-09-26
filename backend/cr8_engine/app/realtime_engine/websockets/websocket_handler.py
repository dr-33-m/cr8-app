"""
WebSocket handler implementation for cr8_engine with B.L.A.Z.E Agent integration.
This module routes all user messages through the B.L.A.Z.E intelligent agent with dynamic addon capabilities.
"""

import logging
import time
import uuid
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

    async def _handle_blender_response(self, username: str, data: Dict[str, Any]):
        """Handle responses from Blender and forward to browser"""

        # Check for registry update events
        if data.get("type") == "registry_updated":
            self.logger.info(
                f"Detected registry update message from Blender for {username}")
            await self._handle_registry_update(username, data)
            # Don't forward registry updates to browser - these are internal
            return

        # Handle command responses that B.L.A.Z.E is waiting for
        message_id = data.get("message_id")
        if message_id and self.blaze_agent:
            try:
                # Forward response to B.L.A.Z.E agent for processing
                self.blaze_agent.handle_command_response(message_id, data)
                self.logger.debug(f"Forwarded response with message_id {message_id} to B.L.A.Z.E agent")
            except Exception as e:
                self.logger.error(f"Error forwarding response to B.L.A.Z.E agent: {str(e)}")

        # Note: refresh_context tracking is now handled in session_manager.forward_message()
        # This avoids the bypass issue where responses go directly through session_manager

        # Check for list_scene_objects responses for context updates
        command = data.get("command", "")
        if command == "list_scene_objects_result" and data.get("status") == "success":
            await self._update_scene_context_from_response(username, data)

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
        
        # Track refresh_context flag for addon commands in session
        if client_type == "browser" and data.get("type") == "addon_command":
            message_id = data.get("message_id")
            refresh_context = data.get("refresh_context", False)
            if message_id and refresh_context:
                session = self.session_manager.get_session(username)
                if session:
                    session.pending_refresh_commands[message_id] = {
                        "addon_id": data.get("addon_id"),
                        "command": data.get("command"),
                        "timestamp": time.time()
                    }
                    self.logger.debug(f"Tracking refresh_context for message_id {message_id}")
        
        await self.session_manager.forward_message(username, data, target)
        self.logger.info(f"Forwarded message from {client_type} to {target}")

    async def _update_scene_context_from_response(self, username: str, data: Dict[str, Any]):
        """Update scene context from list_scene_objects response"""
        try:
            # Parse the nested JSON structure from multi_registry_assets
            response_data = data.get("data", {})
            
            # The response has nested JSON: data.message contains a JSON string with the actual data
            message_json_str = response_data.get("message", "")
            objects_list = []
            
            if message_json_str:
                # Parse the JSON string to get the actual message and data
                import json
                try:
                    parsed_data = json.loads(message_json_str)
                    # The actual objects list is in the 'message' field of the parsed data
                    objects_data = parsed_data.get("message", [])
                    
                    # Check if objects_data is already a list (new format) or needs parsing (old format)
                    if isinstance(objects_data, list):
                        # New format: we already have the detailed objects list
                        objects_list = objects_data
                        self.logger.info(f"Extracted detailed objects list: {len(objects_list)} objects")
                    elif isinstance(objects_data, str):
                        # Old format: parse the "Scene objects: name1, name2" string
                        if objects_data.startswith('Scene objects: '):
                            objects_str = objects_data.replace('Scene objects: ', '')
                            if objects_str.strip():
                                object_names = [obj.strip() for obj in objects_str.split(',') if obj.strip()]
                                # Convert to detailed format (minimal info)
                                objects_list = [{'name': name, 'type': 'UNKNOWN'} for name in object_names]
                                self.logger.info(f"Extracted objects from legacy message: {objects_list}")
                        else:
                            self.logger.warning(f"Legacy message does not start with 'Scene objects: ': {objects_data}")
                    else:
                        self.logger.warning(f"Unexpected message data type: {type(objects_data)}")
                        
                except json.JSONDecodeError:
                    # Fallback: treat as direct message
                    self.logger.debug(f"Could not parse JSON, using direct message: {message_json_str}")
            
            # Update the context manager with the detailed objects list
            session = self.session_manager.get_session(username)
            if session and session.blaze_agent:
                session.blaze_agent.context_manager.update_scene_objects(username, objects_list)
                self.logger.info(f"Updated scene context for {username}: {len(objects_list)} objects")
                if objects_list:
                    object_names = [obj.get('name', 'Unknown') for obj in objects_list]
                    self.logger.debug(f"Scene objects: {', '.join(object_names)}")
                
                # Forward scene context update to connected browser session
                if session.browser_socket and not session.browser_socket_closed:
                    try:
                        scene_update_message = {
                            "type": "scene_context_update",
                            "status": "success",
                            "data": {
                                "objects": objects_list,
                                "timestamp": time.time()
                            }
                        }
                        await session.browser_socket.send_json(scene_update_message)
                        self.logger.info(f"Forwarded scene context update to browser for {username}")
                    except Exception as e:
                        session.browser_socket_closed = True
                        self.logger.error(f"Error forwarding scene context to browser: {str(e)}")
            else:
                self.logger.warning(f"No session or B.L.A.Z.E agent found for {username}")
            
        except Exception as e:
            self.logger.error(f"Error updating scene context from response: {str(e)}")
            import traceback
            traceback.print_exc()

    async def _send_error(self, username: str, message: str):
        """Send error message to browser client"""
        session = self.session_manager.get_session(username)
        if session and session.browser_socket:
            await session.browser_socket.send_json({
                "type": "agent_response",
                "status": "error",
                "message": message
            })