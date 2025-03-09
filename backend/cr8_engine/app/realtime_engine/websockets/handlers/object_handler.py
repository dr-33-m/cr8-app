"""
Object command handlers for WebSocket communication in cr8_engine.
"""

import logging
import uuid
from typing import Dict, Any
from .base_specialized_handler import BaseSpecializedHandler

# Configure logging
logger = logging.getLogger(__name__)


class ObjectHandler(BaseSpecializedHandler):
    """Handlers for object-related WebSocket commands."""

    async def handle_update_object(self, username: str, data: Dict[str, Any], client_type: str) -> None:
        """
        Handle updating object with session awareness.

        Args:
            username: The username of the client
            data: The message data
            client_type: The type of client (browser or blender)
        """
        if client_type != "browser":
            return

        try:
            self.logger.info(f"Handling update_object request from {username}")

            # Extract parameters
            object_name = data.get('object_name')
            location = data.get('location')
            rotation = data.get('rotation')
            scale = data.get('scale')
            message_id = data.get('message_id')

            # Generate message_id if not provided
            if not message_id:
                message_id = str(uuid.uuid4())
                self.logger.debug(f"Generated message_id: {message_id}")

            # Validate required parameters
            if not object_name:
                await self.send_error(username, 'update_object', 'Missing object_name parameter', message_id)
                return

            # Forward the command to Blender
            try:
                session = await self.forward_to_blender(
                    username,
                    'update_object',
                    {
                        'object_name': object_name,
                        'location': location,
                        'rotation': rotation,
                        'scale': scale
                    },
                    message_id
                )

                # Send confirmation to browser
                await self.send_response(
                    username,
                    'update_object_result',
                    True,
                    {
                        'object_name': object_name,
                        'status': 'forwarded_to_blender'
                    },
                    f"Object update request forwarded to Blender",
                    message_id
                )

            except ValueError as ve:
                await self.send_error(username, 'update_object', str(ve), message_id)

        except Exception as e:
            self.logger.error(f"Error handling update_object: {e}")
            import traceback
            traceback.print_exc()
            await self.send_error(username, 'update_object', f"Error: {str(e)}", data.get('message_id'))

    async def handle_object_response(self, username: str, data: Dict[str, Any], client_type: str) -> None:
        """
        Handle responses from object-related commands.

        Args:
            username: The username of the client
            data: The response data
            client_type: The type of client (browser or blender)
        """
        # Use the base class implementation for handling responses
        await self.handle_response(username, data, client_type)
