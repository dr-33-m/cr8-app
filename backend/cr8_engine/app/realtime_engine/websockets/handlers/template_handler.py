"""
Template control handlers for WebSocket communication in cr8_engine.
"""

import logging
import uuid
from typing import Dict, Any
from .base_specialized_handler import BaseSpecializedHandler

# Configure logging
logger = logging.getLogger(__name__)


class TemplateHandler(BaseSpecializedHandler):
    """Handlers for template-related WebSocket commands."""

    async def handle_get_template_controls(self, username: str, data: Dict[str, Any], client_type: str, command: str = None) -> None:
        """Handle getting template controls"""
        if client_type != "browser":
            return

        try:
            self.logger.info(
                f"Handling get_template_controls request from {username}")

            # Generate message_id
            message_id = str(uuid.uuid4())
            self.logger.debug(f"Generated message_id: {message_id}")

            # Forward the command to Blender
            try:
                # Use the command parameter instead of hardcoding 'rescan_template'
                cmd = command if command else 'get_template_controls'
                session = await self.forward_to_blender(
                    username,
                    cmd,
                    {},
                    message_id
                )

                # Send confirmation to browser
                await self.send_response(
                    username,
                    'template_controls_result',
                    True,
                    {
                        'status': 'forwarded_to_blender'
                    },
                    f"Template controls request forwarded to Blender",
                    message_id
                )

            except ValueError as ve:
                await self.send_error(username, 'get_template_controls', str(ve), message_id)

        except Exception as e:
            self.logger.error(f"Error handling get_template_controls: {e}")
            import traceback
            traceback.print_exc()
            await self.send_error(username, 'get_template_controls', f"Error: {str(e)}", data.get('message_id'))

    async def handle_template_controls_response(self, username: str, data: Dict[str, Any], client_type: str) -> None:
        """
        Handle responses from template-related commands.

        Args:
            username: The username of the client
            data: The response data
            client_type: The type of client (browser or blender)
        """
        # Use the base class implementation for handling responses
        await self.handle_response(username, data, client_type)
