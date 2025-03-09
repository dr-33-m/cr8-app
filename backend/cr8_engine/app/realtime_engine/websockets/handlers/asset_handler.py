"""
Asset operation handlers for WebSocket communication in cr8_engine.
"""

import logging
import uuid
from typing import Dict, Any
from .base_specialized_handler import BaseSpecializedHandler

# Configure logging
logger = logging.getLogger(__name__)


class AssetHandler(BaseSpecializedHandler):
    """Handlers for asset-related WebSocket commands."""

    async def handle_append_asset(self, username: str, data: Dict[str, Any], client_type: str) -> None:
        """Handle appending an asset to an empty"""
        if client_type != "browser":
            return

        try:
            self.logger.info(f"Handling append_asset request from {username}")

            # Extract parameters
            empty_name = data.get('empty_name')
            asset_name = data.get('asset_name')
            message_id = data.get('message_id')
            filepath = data.get('filepath')

            # Generate message_id if not provided
            if not message_id:
                message_id = str(uuid.uuid4())
                self.logger.debug(f"Generated message_id: {message_id}")

            # Validate required parameters
            if not empty_name:
                await self.send_error(username, 'append_asset', 'Missing empty_name parameter', message_id)
                return

            if not asset_name:
                await self.send_error(username, 'append_asset', 'Missing asset_name parameter', message_id)
                return

            # Forward the command to Blender
            try:
                session = await self.forward_to_blender(
                    username,
                    'append_asset',
                    {
                        'empty_name': empty_name,
                        'asset_name': asset_name,
                        'filepath': filepath,
                        # Add mode parameter with default 'PLACE'
                        'mode': data.get('mode', 'PLACE'),
                        # Also forward scale_factor
                        'scale_factor': data.get('scale_factor', 1.0),
                        # And center_origin
                        'center_origin': data.get('center_origin', False)
                    },
                    message_id
                )

                # Send confirmation to browser
                await self.send_response(
                    username,
                    'append_asset_result',
                    True,
                    {
                        'empty_name': empty_name,
                        'asset_name': asset_name,
                        'status': 'forwarded_to_blender'
                    },
                    f"Asset append request forwarded to Blender",
                    message_id
                )

            except ValueError as ve:
                await self.send_error(username, 'append_asset', str(ve), message_id)

        except Exception as e:
            self.logger.error(f"Error handling append_asset: {e}")
            import traceback
            traceback.print_exc()
            await self.send_error(username, 'append_asset', f"Error: {str(e)}", data.get('message_id'))

    async def handle_remove_assets(self, username: str, data: Dict[str, Any], client_type: str) -> None:
        """Handle removing assets from an empty"""
        if client_type != "browser":
            return

        try:
            self.logger.info(f"Handling remove_assets request from {username}")

            # Extract parameters
            empty_name = data.get('empty_name')
            message_id = data.get('message_id')

            # Generate message_id if not provided
            if not message_id:
                message_id = str(uuid.uuid4())
                self.logger.debug(f"Generated message_id: {message_id}")

            # Validate required parameters
            if not empty_name:
                await self.send_error(username, 'remove_assets', 'Missing empty_name parameter', message_id)
                return

            # Forward the command to Blender
            try:
                session = await self.forward_to_blender(
                    username,
                    'remove_assets',
                    {
                        'empty_name': empty_name
                    },
                    message_id
                )

                # Send confirmation to browser
                await self.send_response(
                    username,
                    'remove_assets_result',
                    True,
                    {
                        'empty_name': empty_name,
                        'status': 'forwarded_to_blender'
                    },
                    f"Asset removal request forwarded to Blender",
                    message_id
                )

            except ValueError as ve:
                await self.send_error(username, 'remove_assets', str(ve), message_id)

        except Exception as e:
            self.logger.error(f"Error handling remove_assets: {e}")
            import traceback
            traceback.print_exc()
            await self.send_error(username, 'remove_assets', f"Error: {str(e)}", data.get('message_id'))

    async def handle_swap_assets(self, username: str, data: Dict[str, Any], client_type: str) -> None:
        """Handle swapping assets between two empties"""
        if client_type != "browser":
            return

        try:
            self.logger.info(f"Handling swap_assets request from {username}")

            # Extract parameters
            empty1_name = data.get('empty1_name')
            empty2_name = data.get('empty2_name')
            message_id = data.get('message_id')

            # Generate message_id if not provided
            if not message_id:
                message_id = str(uuid.uuid4())
                self.logger.debug(f"Generated message_id: {message_id}")

            # Validate required parameters
            if not empty1_name:
                await self.send_error(username, 'swap_assets', 'Missing empty1_name parameter', message_id)
                return

            if not empty2_name:
                await self.send_error(username, 'swap_assets', 'Missing empty2_name parameter', message_id)
                return

            # Forward the command to Blender
            try:
                session = await self.forward_to_blender(
                    username,
                    'swap_assets',
                    {
                        'empty1_name': empty1_name,
                        'empty2_name': empty2_name
                    },
                    message_id
                )

                # Send confirmation to browser
                await self.send_response(
                    username,
                    'swap_assets_result',
                    True,
                    {
                        'empty1_name': empty1_name,
                        'empty2_name': empty2_name,
                        'status': 'forwarded_to_blender'
                    },
                    f"Asset swap request forwarded to Blender",
                    message_id
                )

            except ValueError as ve:
                await self.send_error(username, 'swap_assets', str(ve), message_id)

        except Exception as e:
            self.logger.error(f"Error handling swap_assets: {e}")
            import traceback
            traceback.print_exc()
            await self.send_error(username, 'swap_assets', f"Error: {str(e)}", data.get('message_id'))

    async def handle_rotate_assets(self, username: str, data: Dict[str, Any], client_type: str) -> None:
        """Handle rotating assets on an empty"""
        if client_type != "browser":
            return

        try:
            self.logger.info(f"Handling rotate_assets request from {username}")

            # Extract parameters
            empty_name = data.get('empty_name')
            degrees = data.get('degrees')
            reset = data.get('reset', False)
            message_id = data.get('message_id')

            # Generate message_id if not provided
            if not message_id:
                message_id = str(uuid.uuid4())
                self.logger.debug(f"Generated message_id: {message_id}")

            # Validate required parameters
            if not empty_name:
                await self.send_error(username, 'rotate_assets', 'Missing empty_name parameter', message_id)
                return

            # Forward the command to Blender
            try:
                session = await self.forward_to_blender(
                    username,
                    'rotate_assets',
                    {
                        'empty_name': empty_name,
                        'degrees': degrees,
                        'reset': reset
                    },
                    message_id
                )

                # Send confirmation to browser
                await self.send_response(
                    username,
                    'rotate_assets_result',
                    True,
                    {
                        'empty_name': empty_name,
                        'status': 'forwarded_to_blender'
                    },
                    f"Asset rotation request forwarded to Blender",
                    message_id
                )

            except ValueError as ve:
                await self.send_error(username, 'rotate_assets', str(ve), message_id)

        except Exception as e:
            self.logger.error(f"Error handling rotate_assets: {e}")
            import traceback
            traceback.print_exc()
            await self.send_error(username, 'rotate_assets', f"Error: {str(e)}", data.get('message_id'))

    async def handle_scale_assets(self, username: str, data: Dict[str, Any], client_type: str) -> None:
        """Handle scaling assets on an empty"""
        if client_type != "browser":
            return

        try:
            self.logger.info(f"Handling scale_assets request from {username}")

            # Extract parameters
            empty_name = data.get('empty_name')
            scale_percent = data.get('scale_percent')
            reset = data.get('reset', False)
            message_id = data.get('message_id')

            # Generate message_id if not provided
            if not message_id:
                message_id = str(uuid.uuid4())
                self.logger.debug(f"Generated message_id: {message_id}")

            # Validate required parameters
            if not empty_name:
                await self.send_error(username, 'scale_assets', 'Missing empty_name parameter', message_id)
                return

            # Forward the command to Blender
            try:
                session = await self.forward_to_blender(
                    username,
                    'scale_assets',
                    {
                        'empty_name': empty_name,
                        'scale_percent': scale_percent,
                        'reset': reset
                    },
                    message_id
                )

                # Send confirmation to browser
                await self.send_response(
                    username,
                    'scale_assets_result',
                    True,
                    {
                        'empty_name': empty_name,
                        'status': 'forwarded_to_blender'
                    },
                    f"Asset scaling request forwarded to Blender",
                    message_id
                )

            except ValueError as ve:
                await self.send_error(username, 'scale_assets', str(ve), message_id)

        except Exception as e:
            self.logger.error(f"Error handling scale_assets: {e}")
            import traceback
            traceback.print_exc()
            await self.send_error(username, 'scale_assets', f"Error: {str(e)}", data.get('message_id'))

    async def handle_get_asset_info(self, username: str, data: Dict[str, Any], client_type: str) -> None:
        """Handle getting asset info from an empty"""
        if client_type != "browser":
            return

        try:
            self.logger.info(
                f"Handling get_asset_info request from {username}")

            # Extract parameters
            empty_name = data.get('empty_name')
            message_id = data.get('message_id')

            # Generate message_id if not provided
            if not message_id:
                message_id = str(uuid.uuid4())
                self.logger.debug(f"Generated message_id: {message_id}")

            # Validate required parameters
            if not empty_name:
                await self.send_error(username, 'get_asset_info', 'Missing empty_name parameter', message_id)
                return

            # Forward the command to Blender
            try:
                session = await self.forward_to_blender(
                    username,
                    'get_asset_info',
                    {
                        'empty_name': empty_name
                    },
                    message_id
                )

                # Send confirmation to browser
                await self.send_response(
                    username,
                    'get_asset_info_result',
                    True,
                    {
                        'empty_name': empty_name,
                        'status': 'forwarded_to_blender'
                    },
                    f"Asset info request forwarded to Blender",
                    message_id
                )

            except ValueError as ve:
                await self.send_error(username, 'get_asset_info', str(ve), message_id)

        except Exception as e:
            self.logger.error(f"Error handling get_asset_info: {e}")
            import traceback
            traceback.print_exc()
            await self.send_error(username, 'get_asset_info', f"Error: {str(e)}", data.get('message_id'))

    async def handle_asset_operation_response(self, username: str, data: Dict[str, Any], client_type: str) -> None:
        """
        Handle responses from asset-related commands.

        Args:
            username: The username of the client
            data: The response data
            client_type: The type of client (browser or blender)
        """
        # Use the base class implementation for handling responses
        await self.handle_response(username, data, client_type)
