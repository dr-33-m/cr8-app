"""
WebSocket handler implementation for cr8_engine.
This module provides the main WebSocket handler class that uses the modular architecture.
"""

import logging
import uuid
from typing import Dict, Any
from fastapi import WebSocket

# Import specialized handlers
from .handlers.animation_handler import AnimationHandler
from .handlers.asset_handler import AssetHandler
from .handlers.template_handler import TemplateHandler
from .handlers.preview_handler import PreviewHandler
from .handlers.camera_handler import CameraHandler
from .handlers.light_handler import LightHandler
from .handlers.material_handler import MaterialHandler
from .handlers.object_handler import ObjectHandler

# Configure logging
logger = logging.getLogger(__name__)


class WebSocketHandler:
    """WebSocket handler that uses the modular architecture."""

    def __init__(self, session_manager, username: str):
        """
        Initialize the WebSocket handler.

        Args:
            session_manager: The session manager instance
            username: The username for this handler
        """
        self.session_manager = session_manager
        self.username = username
        self.logger = logging.getLogger(__name__)

        # Initialize specialized handlers
        self.animation_handler = AnimationHandler(session_manager)
        self.asset_handler = AssetHandler(session_manager)
        self.template_handler = TemplateHandler(session_manager)
        self.preview_handler = PreviewHandler(session_manager)
        self.camera_handler = CameraHandler(session_manager)
        self.light_handler = LightHandler(session_manager)
        self.material_handler = MaterialHandler(session_manager)
        self.object_handler = ObjectHandler(session_manager)

        # Initialize logger
        logger.info(f"WebSocketHandler initialized for user {username}")

    async def handle_message(self, username: str, data: Dict[str, Any], client_type: str):
        """
        Process incoming WebSocket messages with proper routing.

        Args:
            username: The username of the client
            data: The message data
            client_type: The type of client (browser or blender)
        """
        try:
            command = data.get("command")
            action = data.get("action")
            status = data.get("status")

            # Handle connection status messages (case-insensitive check)
            if status and status.lower() == "connected" or command == "connection_status":
                self.logger.info(
                    f"Client {username} connected with status: {status}")
                session = self.session_manager.get_session(username)
                if session and session.browser_socket:
                    retry_delay = min(
                        session.base_retry_delay * (2 ** session.connection_attempts), 60)
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
                    # Check if this is a recovery attempt
                    recovery_mode = data.get("recovery", False)

                    if recovery_mode:
                        # In recovery mode, reset session state if needed
                        session = self.session_manager.get_session(username)
                        if session and session.state != "waiting_for_browser_ready":
                            # Force session into the correct state for recovery
                            session.state = "waiting_for_browser_ready"
                            self.logger.info(
                                f"Resetting session state for {username} in recovery mode")

                    # Then continue with normal launch logic
                    await self.session_manager.launch_blender_for_session(username)

                    # Notify browser that Blender is being launched
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
                    # Notify browser of the error
                    session = self.session_manager.get_session(username)
                    if session and session.browser_socket:
                        await session.browser_socket.send_json({
                            "type": "system",
                            "status": "error",
                            "message": f"Failed to launch Blender: {str(e)}"
                        })
                return

            # Command completion handler
            if status == "completed":
                await self._handle_command_completion(username, data)
                return

            # Check for animation-related commands
            if (command and command.startswith('load_') and command.endswith('_animation')) or command == 'get_animations':
                await self._route_to_animation_handler(username, data, client_type, command)
                return

            # Check for asset-related commands
            if command in ['append_asset', 'remove_assets', 'swap_assets',
                           'rotate_assets', 'scale_assets', 'get_asset_info']:
                await self._route_to_asset_handler(username, data, client_type, command)
                return

            # Check for animation-related responses
            if command and 'animation' in command and '_result' in command:
                await self.animation_handler.handle_animation_response(username, data, client_type)
                return

            # Check for asset-related responses
            if command and 'asset' in command and '_result' in command:
                await self.asset_handler.handle_asset_operation_response(username, data, client_type)
                return

            # Check for template-related commands
            if command == 'get_template_controls':
                await self._route_to_template_handler(username, data, client_type, command)
                return

            # Check for template-related responses
            if command and 'template' in command and '_result' in command:
                await self.template_handler.handle_template_controls_response(username, data, client_type)
                return

            # Check for scene control commands
            if command == 'update_camera':
                await self.camera_handler.handle_update_camera(username, data, client_type)
                return

            if command == 'update_light':
                await self.light_handler.handle_update_light(username, data, client_type)
                return

            if command == 'update_material':
                await self.material_handler.handle_update_material(username, data, client_type)
                return

            if command == 'update_object':
                await self.object_handler.handle_update_object(username, data, client_type)
                return

            # Check for scene control responses
            if command and '_result' in command:
                if 'camera' in command:
                    await self.camera_handler.handle_camera_response(username, data, client_type)
                    return
                elif 'light' in command:
                    await self.light_handler.handle_light_response(username, data, client_type)
                    return
                elif 'material' in command:
                    await self.material_handler.handle_material_response(username, data, client_type)
                    return
                elif 'object' in command:
                    await self.object_handler.handle_object_response(username, data, client_type)
                    return

            # Check for preview-related commands
            if command in ['start_preview_rendering', 'stop_broadcast',
                           'start_broadcast', 'generate_video']:
                await self._route_to_preview_handler(username, data, client_type, command)
                return

            # If no handler found, forward the message to the other client type
            target = "blender" if client_type == "browser" else "browser"
            await self.session_manager.forward_message(username, data, target)
            self.logger.info(
                f"Forwarded message from {client_type} to {target}: {command or action}")

        except Exception as e:
            self.logger.error(f"Message processing error: {str(e)}")
            session = self.session_manager.get_session(username)
            if session:
                target_socket = session.browser_socket if client_type == "blender" else session.blender_socket
                if target_socket:
                    await target_socket.send_json({
                        "status": "ERROR",
                        "message": f"Message processing error: {str(e)}"
                    })

    async def _route_to_animation_handler(self, username: str, data: Dict[str, Any], client_type: str, command: str):
        """Route animation-related commands to the animation handler"""
        if command == 'load_camera_animation':
            await self.animation_handler.handle_load_camera_animation(username, data, client_type)
        elif command == 'load_light_animation':
            await self.animation_handler.handle_load_light_animation(username, data, client_type)
        elif command == 'load_product_animation':
            await self.animation_handler.handle_load_product_animation(username, data, client_type)
        elif command == 'get_animations':
            await self.animation_handler.handle_get_animations(username, data, client_type)

    async def _route_to_asset_handler(self, username: str, data: Dict[str, Any], client_type: str, command: str):
        """Route asset-related commands to the asset handler"""
        if command == 'append_asset':
            await self.asset_handler.handle_append_asset(username, data, client_type)
        elif command == 'remove_assets':
            await self.asset_handler.handle_remove_assets(username, data, client_type)
        elif command == 'swap_assets':
            await self.asset_handler.handle_swap_assets(username, data, client_type)
        elif command == 'rotate_assets':
            await self.asset_handler.handle_rotate_assets(username, data, client_type)
        elif command == 'scale_assets':
            await self.asset_handler.handle_scale_assets(username, data, client_type)
        elif command == 'get_asset_info':
            await self.asset_handler.handle_get_asset_info(username, data, client_type)

    async def _route_to_template_handler(self, username: str, data: Dict[str, Any], client_type: str, command: str):
        """Route template-related commands to the template handler"""
        if command == 'get_template_controls':
            await self.template_handler.handle_get_template_controls(username, data, client_type, command)

    async def _route_to_preview_handler(self, username: str, data: Dict[str, Any], client_type: str, command: str):
        """Route preview-related commands to the preview handler"""
        if command == 'start_preview_rendering':
            await self.preview_handler.handle_preview_rendering(username, data, client_type)
        elif command == 'generate_video':
            await self.preview_handler.handle_generate_video(username, data, client_type)
        elif command == 'start_broadcast':
            await self.preview_handler.handle_start_broadcast(username, data, client_type)
        elif command == 'stop_broadcast':
            await self.preview_handler.handle_stop_broadcast(username, data, client_type)

    async def _handle_command_completion(self, username: str, data: Dict[str, Any]):
        """Handle command completion"""
        session = self.session_manager.get_session(username)
        if not session or not session.browser_socket:
            return

        await session.browser_socket.send_json({
            "type": "command_completed",
            "command": data.get("command", "unknown"),
            "message_id": data.get("message_id"),
            "status": "success"
        })

    async def _send_error(self, username: str, message: str):
        """Send error message to browser client"""
        session = self.session_manager.get_session(username)
        if session and session.browser_socket:
            await session.browser_socket.send_json({
                "status": "ERROR",
                "message": message
            })
