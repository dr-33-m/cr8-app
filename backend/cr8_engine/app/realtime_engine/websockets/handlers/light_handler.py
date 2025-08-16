"""
Light command handlers for WebSocket communication in cr8_engine.
"""

import logging
import uuid
from typing import Dict, Any
from .base_specialized_handler import BaseSpecializedHandler

# Configure logging
logger = logging.getLogger(__name__)


class LightHandler(BaseSpecializedHandler):
    """Handlers for light-related WebSocket commands."""

    async def handle_update_light(self, username: str, data: Dict[str, Any], client_type: str) -> None:
        """
        Handle updating light with session awareness.

        Args:
            username: The username of the client
            data: The message data
            client_type: The type of client (browser or blender)
        """
        if client_type not in ["browser", "agent"]:
            return

        try:
            self.logger.info(f"Handling update_light request from {username}")

            # Extract parameters
            light_name = data.get('light_name')
            color = data.get('color')
            strength = data.get('strength')
            message_id = data.get('message_id')

            # Generate message_id if not provided
            if not message_id:
                message_id = str(uuid.uuid4())
                self.logger.debug(f"Generated message_id: {message_id}")

            # Validate required parameters
            if not light_name:
                await self.send_error(username, 'update_light', 'Missing light_name parameter', message_id)
                return

            # Forward the command to Blender
            try:
                session = await self.forward_to_blender(
                    username,
                    'update_light',
                    {
                        'light_name': light_name,
                        'color': color,
                        'strength': strength
                    },
                    message_id
                )

                # Send confirmation to browser
                await self.send_response(
                    username,
                    'update_light_result',
                    True,
                    {
                        'light_name': light_name,
                        'status': 'forwarded_to_blender'
                    },
                    f"Light update request forwarded to Blender",
                    message_id
                )

            except ValueError as ve:
                await self.send_error(username, 'update_light', str(ve), message_id)

        except Exception as e:
            self.logger.error(f"Error handling update_light: {e}")
            import traceback
            traceback.print_exc()
            await self.send_error(username, 'update_light', f"Error: {str(e)}", data.get('message_id'))

    async def handle_light_response(self, username: str, data: Dict[str, Any], client_type: str) -> None:
        """
        Handle responses from light-related commands.

        Args:
            username: The username of the client
            data: The response data
            client_type: The type of client (browser or blender)
        """
        # Use the base class implementation for handling responses
        await self.handle_response(username, data, client_type)
