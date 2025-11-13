"""
Command Executor - Handles WebSocket command execution and response management
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from pydantic_ai import ModelRetry
from app.lib import generate_message_id

logger = logging.getLogger(__name__)


class CommandExecutor:
    """Executes addon commands via WebSocket and manages responses"""

    def __init__(self, agent_instance, screenshot_manager, socketio_instance=None):
        """Initialize command executor with agent instance"""
        self.agent_instance = agent_instance
        self.screenshot_manager = screenshot_manager
        self.socketio = socketio_instance
        self.pending_responses = {}  # message_id -> Future

    async def execute_addon_command(self, addon_id: str, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute command on addon via WebSocket with response waiting and error handling"""
        try:
            if not self.agent_instance.current_username:
                raise ModelRetry("No active user session available")

            logger.info(f"Executing {addon_id}.{command} with params: {params}")

            # Send command and wait for response
            response = await self._send_command_and_wait_response(addon_id, command, params)

            # Parse response status from SocketMessage payload
            payload = response.get('payload', {})
            if payload.get('status') == 'error':
                # Extract error details from payload
                error_data = payload.get('data', {})
                error_msg = error_data.get('message', 'Unknown error occurred')
                logger.error(f"Command {command} failed: {error_msg}")
                raise ModelRetry(f"Command {command} failed: {error_msg}")
            elif payload.get('status') == 'success':
                # Extract success details from payload
                success_data = payload.get('data', {})
                success_msg = success_data.get('message', 'Command completed')
                logger.info(f"Command {command} succeeded: {success_msg}")

                # Store screenshot data for later processing if present
                if self.screenshot_manager and 'image_data' in success_data and 'media_type' in success_data:
                    self.screenshot_manager.store_screenshot(success_data, self.agent_instance.current_username)
                    width = success_data.get('width', 'unknown')
                    height = success_data.get('height', 'unknown')
                    logger.info(f"Stored screenshot data for analysis ({width}x{height})")

                # Return the actual response data for parsing by caller
                return response
            else:
                raise ModelRetry(f"Unexpected response from {command}: {response}")

        except ModelRetry:
            raise  # Re-raise ModelRetry for Pydantic AI to handle
        except Exception as e:
            logger.error(f"Error executing addon command: {str(e)}")
            raise ModelRetry(f"Error executing {command}: {str(e)}")

    async def _send_command_and_wait_response(self, addon_id: str, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send command via unified routing system and wait for response"""
        # Create unique message ID using standardized utility
        message_id = generate_message_id()

        # Set up response waiting
        response_future = asyncio.Future()
        self.pending_responses[message_id] = response_future

        try:
            # Create command message
            command_data = {
                "type": "addon_command",
                "addon_id": addon_id,
                "command": command,
                "params": params,
                "message_id": message_id,
                "metadata": {
                    "route": self.agent_instance.current_route
                }
            }

            # Use unified send_command_to_blender() method with preserved route
            # This ensures all commands (direct or agent-initiated) use the same routing
            # Route is preserved from the original frontend request
            success = await self.agent_instance.blender_namespace.send_command_to_blender(
                self.agent_instance.current_username,
                command_data,
                route=self.agent_instance.current_route
            )

            if not success:
                raise Exception(f"Failed to send command {command} to Blender")

            logger.debug(f"Sent command {command} with message_id {message_id} via unified routing")

            # Wait for response (no timeout - Blender will always respond)
            response = await response_future

            return response

        finally:
            # Cleanup pending response
            self.pending_responses.pop(message_id, None)

    def handle_command_response(self, message_id: str, response_data: Dict[str, Any]):
        """Handle incoming command responses from WebSocket"""
        try:
            if message_id in self.pending_responses:
                future = self.pending_responses[message_id]
                if not future.done():
                    future.set_result(response_data)
                    logger.debug(f"Resolved response for message_id {message_id}")
                else:
                    logger.warning(f"Response future for {message_id} already resolved")
            else:
                logger.warning(f"No pending response found for message_id {message_id}")
        except Exception as e:
            logger.error(f"Error handling command response: {str(e)}")
