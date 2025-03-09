"""
Animation command handlers for WebSocket communication in cr8_engine.
"""

import logging
import uuid
from typing import Dict, Any, Optional
from .base_specialized_handler import BaseSpecializedHandler
from app.db.session import get_db

# Configure logging
logger = logging.getLogger(__name__)


class AnimationHandler(BaseSpecializedHandler):
    """Handlers for animation-related WebSocket commands."""

    async def handle_load_camera_animation(self, username: str, data: Dict[str, Any], client_type: str) -> None:
        """
        Handle loading camera animation with session awareness.

        Args:
            username: The username of the client
            data: The message data
            client_type: The type of client (browser or blender)
        """
        # Only process requests from browser clients
        if client_type != "browser":
            return

        try:
            self.logger.info(
                f"Handling load_camera_animation request from {username}")

            # Extract parameters
            animation_id = data.get('animation_id')
            empty_name = data.get('empty_name')
            message_id = data.get('message_id')

            # Generate message_id if not provided
            if not message_id:
                message_id = str(uuid.uuid4())
                self.logger.debug(f"Generated message_id: {message_id}")

            # Validate required parameters
            if not animation_id:
                await self.send_error(username, 'load_camera_animation', 'Missing animation_id parameter', message_id)
                return

            if not empty_name:
                await self.send_error(username, 'load_camera_animation', 'Missing empty_name parameter', message_id)
                return

            # Fetch animation data from database
            db = get_db()
            result = db.table("template").select(
                "*").eq("id", animation_id).execute()

            if not result.data or len(result.data) == 0:
                await self.send_error(username, 'load_camera_animation', f'Animation {animation_id} not found', message_id)
                return

            template = result.data[0]
            template_data = template.get("templateData", {})

            # Prepare the message to forward to Blender
            blender_data = {
                'empty_name': empty_name,
                'template_data': template_data,
                'message_id': message_id
            }

            try:
                # Forward to Blender using the base class method
                session = await self.forward_to_blender(
                    username,
                    "load_camera_animation",
                    blender_data,
                    message_id
                )

                # Send confirmation to browser
                await self.send_response(
                    username,
                    'camera_animation_result',
                    True,
                    {
                        'animation_id': animation_id,
                        'empty_name': empty_name,
                        'status': 'forwarded_to_blender'
                    },
                    f"Camera animation request forwarded to Blender",
                    message_id
                )

            except ValueError as ve:
                await self.send_error(username, 'load_camera_animation', str(ve), message_id)

        except Exception as e:
            self.logger.error(f"Error handling load_camera_animation: {e}")
            import traceback
            traceback.print_exc()
            await self.send_error(username, 'load_camera_animation', f"Error: {str(e)}", data.get('message_id'))

    async def handle_load_light_animation(self, username: str, data: Dict[str, Any], client_type: str) -> None:
        """
        Handle loading light animation with session awareness.

        Args:
            username: The username of the client
            data: The message data
            client_type: The type of client (browser or blender)
        """
        # Only process requests from browser clients
        if client_type != "browser":
            return

        try:
            self.logger.info(
                f"Handling load_light_animation request from {username}")

            # Extract parameters
            animation_id = data.get('animation_id')
            empty_name = data.get('empty_name')
            message_id = data.get('message_id')

            # Generate message_id if not provided
            if not message_id:
                message_id = str(uuid.uuid4())
                self.logger.debug(f"Generated message_id: {message_id}")

            # Validate required parameters
            if not animation_id:
                await self.send_error(username, 'load_light_animation', 'Missing animation_id parameter', message_id)
                return

            if not empty_name:
                await self.send_error(username, 'load_light_animation', 'Missing empty_name parameter', message_id)
                return

            # Fetch animation data from database
            db = get_db()
            result = db.table("template").select(
                "*").eq("id", animation_id).execute()

            if not result.data or len(result.data) == 0:
                await self.send_error(username, 'load_light_animation', f'Animation {animation_id} not found', message_id)
                return

            template = result.data[0]
            template_data = template.get("templateData", {})

            # Prepare the message to forward to Blender
            blender_data = {
                'empty_name': empty_name,
                'template_data': template_data,
                'message_id': message_id
            }

            try:
                # Forward to Blender using the base class method
                session = await self.forward_to_blender(
                    username,
                    "load_light_animation",
                    blender_data,
                    message_id
                )

                # Send confirmation to browser
                await self.send_response(
                    username,
                    'light_animation_result',
                    True,
                    {
                        'animation_id': animation_id,
                        'empty_name': empty_name,
                        'status': 'forwarded_to_blender'
                    },
                    f"Light animation request forwarded to Blender",
                    message_id
                )

            except ValueError as ve:
                await self.send_error(username, 'load_light_animation', str(ve), message_id)

        except Exception as e:
            self.logger.error(f"Error handling load_light_animation: {e}")
            import traceback
            traceback.print_exc()
            await self.send_error(username, 'load_light_animation', f"Error: {str(e)}", data.get('message_id'))

    async def handle_load_product_animation(self, username: str, data: Dict[str, Any], client_type: str) -> None:
        """
        Handle loading product animation with session awareness.

        Args:
            username: The username of the client
            data: The message data
            client_type: The type of client (browser or blender)
        """
        # Only process requests from browser clients
        if client_type != "browser":
            return

        try:
            self.logger.info(
                f"Handling load_product_animation request from {username}")

            # Extract parameters
            animation_id = data.get('animation_id')
            empty_name = data.get('empty_name')
            message_id = data.get('message_id')

            # Generate message_id if not provided
            if not message_id:
                message_id = str(uuid.uuid4())
                self.logger.debug(f"Generated message_id: {message_id}")

            # Validate required parameters
            if not animation_id:
                await self.send_error(username, 'load_product_animation', 'Missing animation_id parameter', message_id)
                return

            if not empty_name:
                await self.send_error(username, 'load_product_animation', 'Missing empty_name parameter', message_id)
                return

            # Fetch animation data from database
            db = get_db()
            result = db.table("template").select(
                "*").eq("id", animation_id).execute()

            if not result.data or len(result.data) == 0:
                await self.send_error(username, 'load_product_animation', f'Animation {animation_id} not found', message_id)
                return

            template = result.data[0]
            template_data = template.get("templateData", {})

            # Prepare the message to forward to Blender
            blender_data = {
                'empty_name': empty_name,
                'template_data': template_data,
                'message_id': message_id
            }

            try:
                # Forward to Blender using the base class method
                session = await self.forward_to_blender(
                    username,
                    "load_product_animation",
                    blender_data,
                    message_id
                )

                # Send confirmation to browser
                await self.send_response(
                    username,
                    'product_animation_result',
                    True,
                    {
                        'animation_id': animation_id,
                        'empty_name': empty_name,
                        'status': 'forwarded_to_blender'
                    },
                    f"Product animation request forwarded to Blender",
                    message_id
                )

            except ValueError as ve:
                await self.send_error(username, 'load_product_animation', str(ve), message_id)

        except Exception as e:
            self.logger.error(f"Error handling load_product_animation: {e}")
            import traceback
            traceback.print_exc()
            await self.send_error(username, 'load_product_animation', f"Error: {str(e)}", data.get('message_id'))

    async def handle_get_animations(self, username: str, data: Dict[str, Any], client_type: str) -> None:
        """
        Handle retrieving animations of a specific type with session awareness.

        Args:
            username: The username of the client
            data: The message data
            client_type: The type of client (browser or blender)
        """
        # Only process requests from browser clients
        if client_type != "browser":
            return

        try:
            self.logger.info(
                f"Handling get_animations request from {username}")

            # Extract parameters
            animation_type = data.get('animation_type')
            message_id = data.get('message_id')

            # Generate message_id if not provided
            if not message_id:
                message_id = str(uuid.uuid4())
                self.logger.debug(f"Generated message_id: {message_id}")

            # Validate required parameters
            if not animation_type:
                await self.send_error(username, 'get_animations', 'Missing animation_type parameter', message_id)
                return

            # Validate animation_type
            if animation_type not in ['camera', 'light', 'product']:
                await self.send_error(username, 'get_animations', f'Invalid animation_type: {animation_type}', message_id)
                return

            # TODO: Implement the actual retrieval of animations from the database
            # For now, we'll just return some dummy animations

            # Create dummy animations based on type
            animations = []
            if animation_type == 'camera':
                animations = [
                    {
                        'id': 'cam_anim_1',
                        'name': 'Orbit Camera',
                        'description': 'Camera orbits around the subject',
                        'template_type': 'camera',
                        'duration': 60,
                        'templateData': {
                            'name': 'orbit_camera',
                            'focal_length': 50,
                            'animation_data': {}
                        }
                    },
                    {
                        'id': 'cam_anim_2',
                        'name': 'Zoom In',
                        'description': 'Camera zooms in on the subject',
                        'template_type': 'camera',
                        'duration': 30,
                        'templateData': {
                            'name': 'zoom_in',
                            'focal_length': 35,
                            'animation_data': {}
                        }
                    }
                ]
            elif animation_type == 'light':
                animations = [
                    {
                        'id': 'light_anim_1',
                        'name': 'Pulsing Light',
                        'description': 'Light pulses on and off',
                        'template_type': 'light',
                        'duration': 45,
                        'templateData': {
                            'name': 'pulsing_light',
                            'lights': [
                                {
                                    'light_settings': {
                                        'type': 'POINT',
                                        'energy': 100
                                    },
                                    'animation_data': {}
                                }
                            ]
                        }
                    },
                    {
                        'id': 'light_anim_2',
                        'name': 'Color Shift',
                        'description': 'Light changes color over time',
                        'template_type': 'light',
                        'duration': 60,
                        'templateData': {
                            'name': 'color_shift',
                            'lights': [
                                {
                                    'light_settings': {
                                        'type': 'POINT',
                                        'energy': 150
                                    },
                                    'animation_data': {}
                                }
                            ]
                        }
                    }
                ]
            elif animation_type == 'product':
                animations = [
                    {
                        'id': 'prod_anim_1',
                        'name': 'Rotate Product',
                        'description': 'Product rotates 360 degrees',
                        'template_type': 'product_animation',
                        'duration': 60,
                        'templateData': {
                            'name': 'rotate_product',
                            'base_rotation_mode': 'XYZ',
                            'animation_data': {
                                'fcurves': []
                            }
                        }
                    },
                    {
                        'id': 'prod_anim_2',
                        'name': 'Bounce Product',
                        'description': 'Product bounces up and down',
                        'template_type': 'product_animation',
                        'duration': 45,
                        'templateData': {
                            'name': 'bounce_product',
                            'base_rotation_mode': 'XYZ',
                            'animation_data': {
                                'fcurves': []
                            }
                        }
                    }
                ]

            # Send the animations back to the client
            await self.send_response(
                username,
                'get_animations_result',
                True,
                {
                    'animations': animations,
                    'animation_type': animation_type,
                    'count': len(animations)
                },
                f"Retrieved {len(animations)} {animation_type} animations",
                message_id
            )

        except Exception as e:
            self.logger.error(f"Error handling get_animations: {e}")
            import traceback
            traceback.print_exc()
            await self.send_error(username, 'get_animations', f"Error: {str(e)}", data.get('message_id'))

    async def handle_animation_response(self, username: str, data: Dict[str, Any], client_type: str) -> None:
        """
        Handle responses from animation-related commands.

        Args:
            username: The username of the client
            data: The response data
            client_type: The type of client (browser or blender)
        """
        # Use the base class implementation for handling responses
        await self.handle_response(username, data, client_type)
