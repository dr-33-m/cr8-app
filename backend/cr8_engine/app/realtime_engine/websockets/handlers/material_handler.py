"""
Material command handlers for WebSocket communication in cr8_engine.
"""

import logging
import uuid
from typing import Dict, Any
from .base_specialized_handler import BaseSpecializedHandler

# Configure logging
logger = logging.getLogger(__name__)


class MaterialHandler(BaseSpecializedHandler):
    """Handlers for material-related WebSocket commands."""

    async def handle_update_material(self, username: str, data: Dict[str, Any], client_type: str) -> None:
        """
        Handle updating material with session awareness.

        Args:
            username: The username of the client
            data: The message data
            client_type: The type of client (browser or blender)
        """
        if client_type not in ["browser", "agent"]:
            return

        try:
            self.logger.info(
                f"Handling update_material request from {username}")

            # Extract parameters
            material_name = data.get('material_name')
            color = data.get('color')
            roughness = data.get('roughness')
            metallic = data.get('metallic')
            message_id = data.get('message_id')

            # Generate message_id if not provided
            if not message_id:
                message_id = str(uuid.uuid4())
                self.logger.debug(f"Generated message_id: {message_id}")

            # Validate required parameters
            if not material_name:
                await self.send_error(username, 'update_material', 'Missing material_name parameter', message_id)
                return

            # Forward the command to Blender
            try:
                session = await self.forward_to_blender(
                    username,
                    'update_material',
                    {
                        'material_name': material_name,
                        'color': color,
                        'roughness': roughness,
                        'metallic': metallic
                    },
                    message_id
                )

                # Send confirmation to browser
                await self.send_response(
                    username,
                    'update_material_result',
                    True,
                    {
                        'material_name': material_name,
                        'status': 'forwarded_to_blender'
                    },
                    f"Material update request forwarded to Blender",
                    message_id
                )

            except ValueError as ve:
                await self.send_error(username, 'update_material', str(ve), message_id)

        except Exception as e:
            self.logger.error(f"Error handling update_material: {e}")
            import traceback
            traceback.print_exc()
            await self.send_error(username, 'update_material', f"Error: {str(e)}", data.get('message_id'))

    async def handle_material_response(self, username: str, data: Dict[str, Any], client_type: str) -> None:
        """
        Handle responses from material-related commands.

        Args:
            username: The username of the client
            data: The response data
            client_type: The type of client (browser or blender)
        """
        # Use the base class implementation for handling responses
        await self.handle_response(username, data, client_type)
