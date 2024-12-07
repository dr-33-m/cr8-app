import asyncio
import json
import logging
from typing import Dict, Any

import numpy as np
import websockets

from src import WebSocketConnectionManager


class WebSocketServer:
    """Main WebSocket server with modular command handling."""

    def __init__(self):
        """Initialize the WebSocket server with connection management."""
        self.logger = logging.getLogger(__name__)
        self.connection_manager = WebSocketConnectionManager()

    async def handle_command(self, websocket: websockets.WebSocketServerProtocol, data: Dict[str, Any]):
        """
        Route and handle different commands with extensible design.

        :param websocket: WebSocket connection
        :param data: Parsed JSON data
        """
        try:
            # Extract command, giving preference to 'command' key
            command = data.get("command")
            action = data.get("action")

            command_handlers = {
                "start_preview_rendering": self.preview_rendering_handler,
                "stop_broadcast": self.stop_broadcast_handler,
                "start_broadcast": self.start_broadcast_handler,
                # Add more commands as needed
            }

            self.logger.debug(f"Received action: {action}, command: {command}")
            handler_func = command_handlers.get(action or command)

            if handler_func:
                await handler_func(websocket, data)
            else:
                self.logger.warning(f"Unhandled command: {command} for {data}")

        except Exception as e:
            self.logger.error(f"Command processing error: {e}")

    async def preview_rendering_handler(self, websocket: websockets.WebSocketServerProtocol, params):
        """Forward preview rendering command to Blender client."""
        self.logger.info(f"Handling preview rendering with params: {params}")

        blender_client = self.connection_manager.connections.get('blender')
        if blender_client:
            command = params.get("command")
            _params = params.get("params")
            command = {
                "command": command,
                "params": _params
            }
            await self.connection_manager.send_message(blender_client, command)

            # Send confirmation back to the original websocket
            await self.connection_manager.send_message(websocket, {
                "status": "OK",
                "message": "Preview rendering started"
            })
        else:
            self.logger.warning("Blender client not connected.")
            # Send error back to the original websocket
            await self.connection_manager.send_message(websocket, {
                "status": "ERROR",
                "message": "Blender client not connected"
            })

    async def start_broadcast_handler(self, websocket: websockets.WebSocketServerProtocol, data: Dict[str, Any]):
        """Handle setting the broadcast event for frame rendering."""
        self.logger.info("Setting frame broadcast event")
        self.connection_manager.frame_broadcast_event.set()
        # Optional: Start broadcast task if not already running
        asyncio.create_task(self.connection_manager.broadcast_frame())

    async def stop_broadcast_handler(self, websocket: websockets.WebSocketServerProtocol):
        """
       Stop broadcasting frames when the WebSocket connection is closed.
       """
        self.logger.info("stopping frame broadcast")
        self.connection_manager.stop_broadcast_event.set()
        await self.connection_manager.send_message(websocket, {
            "status": "OK",
            "message": "Frame broadcast stopped"
        })

    async def handle_websocket(self, websocket: websockets.WebSocketServerProtocol):
        """
        Main WebSocket connection handler with comprehensive error management.

        :param websocket: Incoming WebSocket connection
        """
        # Extract client_id from the websocket's path
        client_id = websocket.request.path.lstrip('/')
        self.logger.info(f"Client ID: {client_id}")
        self.connection_manager.register_connection(client_id, websocket)

        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_command(websocket, data)
                except json.JSONDecodeError:
                    self.logger.error(
                        f"Invalid JSON from {client_id}: {message}")
                except Exception as e:
                    self.logger.error(
                        f"Error processing message from {client_id}: {e}")

        except websockets.exceptions.ConnectionClosed:
            self.logger.info(f"Connection closed for {client_id}")
        except Exception as e:
            self.logger.error(f"Unexpected error in WebSocket handler: {e}")
        finally:
            self.connection_manager.unregister_connection(client_id)

    async def start_server(self, host='localhost', port=5001):
        """
        Start the WebSocket server.

        :param host: Hosting address
        :param port: Port number
        """
        server = await websockets.serve(self.handle_websocket, host, port)
        self.logger.info(f"WebSocket server started on {host}:{port}")
        await server.wait_closed()
