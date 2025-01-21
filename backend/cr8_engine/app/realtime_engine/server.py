import asyncio
import json
import logging
from typing import Dict, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
import uuid
from .connection_manager import WebSocketConnectionManager


class WebSocketServer:
    """Main WebSocket server with modular command handling for FastAPI."""

    def __init__(self):
        """Initialize the WebSocket server with connection management."""
        self.logger = logging.getLogger(__name__)
        self.connection_manager = WebSocketConnectionManager()
        self.pending_template_requests = {}

    async def handle_command(self, websocket: WebSocket, data: Dict[str, Any]):
        """
        Route and handle different commands with extensible design.

        :param websocket: WebSocket connection
        :param data: Parsed JSON data
        """
        try:
            # Extract command, giving preference to 'command' key
            command = data.get("command")
            action = data.get("action")
            status = data.get("status")
            message_id = data.get("message_id")

            if status == "Connected":
                self.logger.info(f"Client connected: {websocket.client.host}")
                return

            # Add a new handler for command completion
            if status == "completed":
                await self.handle_command_completion(websocket, data)
                return

            command_handlers = {
                "start_preview_rendering": self.preview_rendering_handler,
                "stop_broadcast": self.stop_broadcast_handler,
                "start_broadcast": self.start_broadcast_handler,
                "generate_video": self.generate_video_handler,
                "get_template_controls": self.get_template_controls,
                "template_controls": self.handle_template_controls_response,
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
            await self.connection_manager.send_message(websocket, {
                "status": "ERROR",
                "message": f"Command processing error: {str(e)}"
            })

    async def preview_rendering_handler(self, websocket: WebSocket, params):
        """Forward preview rendering command to Blender client."""
        self.logger.info(f"Handling preview rendering with params: {params}")
        message_id = str(uuid.uuid4())

        blender_client = self.connection_manager.connections.get('blender')
        if blender_client:
            command = params.get("command")
            _params = params.get("params")
            command = {
                "command": command,
                "params": _params,
                "message_id": message_id
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

    async def generate_video_handler(self, websocket: WebSocket, params):
        """Forward video generation command to Blender client with enhanced command tracking."""
        try:
            # Log the incoming request
            self.logger.info(
                f"Handling video generation request")

            # Get the Blender client connection
            blender_client = self.connection_manager.connections.get('blender')

            # Check if Blender client is connected
            if not blender_client:
                self.logger.warning("Blender client not connected.")
                await self.connection_manager.send_message(websocket, {
                    "status": "ERROR",
                    "message": "Blender client not connected",
                    "code": "BLENDER_DISCONNECTED"
                })
                return

            # Forward message to Blender client with unique ID
            await self.connection_manager.send_message(blender_client, params)

            # Send confirmation to original websocket
            await self.connection_manager.send_message(websocket, {
                "status": "OK",
                "message": "Video generation started",
                "timestamp": datetime.now().isoformat()
            })

            self.logger.info(
                f"Video generation request forwarded successfully")

        except Exception as e:
            self.logger.error(
                f"Unexpected error in video generation handler: {str(e)}")
            try:
                await self.connection_manager.send_message(websocket, {
                    "status": "ERROR",
                    "message": "Internal server error during video generation",
                    "code": "INTERNAL_SERVER_ERROR"
                })
            except Exception as send_error:
                self.logger.critical(
                    f"Failed to send error message: {send_error}")

    async def start_broadcast_handler(self, websocket: WebSocket, data: Dict[str, Any]):
        """Handle setting the broadcast event for frame rendering."""
        self.logger.info("Setting frame broadcast event")

        # Clear stop event to ensure broadcasting can start
        self.connection_manager.stop_broadcast_event.clear()

        # Set the frame broadcasting event to trigger the broadcast loop
        self.connection_manager.frame_broadcast_event.set()

        # Start broadcast task if not already running
        if not self.connection_manager.broadcast_task or self.connection_manager.broadcast_task.done():
            self.logger.info("Starting new broadcast task.")
            self.connection_manager.broadcast_task = asyncio.create_task(
                self.connection_manager.broadcast_frame())

    async def stop_broadcast_handler(self, websocket: WebSocket, data: Dict[str, Any]):
        """
        Stop broadcasting frames when requested.
        """
        self.logger.info("Stopping frame broadcast")
        try:
            # Set the stop event to signal the broadcasting loop to stop
            self.connection_manager.stop_broadcast_event.set()

            # Clear the frame broadcast event to unblock any waiting
            self.connection_manager.frame_broadcast_event.clear()

            # Cancel the broadcast task if it exists and is still running
            if (
                self.connection_manager.broadcast_task
                and not self.connection_manager.broadcast_task.done()
            ):
                self.connection_manager.broadcast_task.cancel()
                try:
                    # Await the task to ensure proper cancellation
                    await self.connection_manager.broadcast_task
                except asyncio.CancelledError:
                    self.logger.info("Broadcast task successfully canceled.")

            # Send a success response back to the client
            await self.connection_manager.send_message(websocket, {
                "status": "OK",
                "message": "Frame broadcast stopped"
            })
        except WebSocketDisconnect:
            # Handle the case where the client disconnects while sending the message
            self.logger.warning(
                "Client disconnected while sending stop broadcast message"
            )
        except Exception as e:
            self.logger.error(f"Error stopping frame broadcast: {e}")

    async def get_template_controls(self, websocket: WebSocket, data: Dict[str, Any]):
        """
        Retrieve controls for a specific template from Blender client.
        """
        self.logger.info(
            f"Handling get template controls request with data: {data}")
        message_id = str(uuid.uuid4())

        # Store the requesting websocket for later response
        self.pending_template_requests[message_id] = websocket

        blender_client = self.connection_manager.connections.get('blender')
        if blender_client:
            command = {
                "command": "rescan_template",
                "message_id": message_id
            }
            await self.connection_manager.send_message(blender_client, command)

            # Send confirmation back to the original websocket
            await self.connection_manager.send_message(websocket, {
                "status": "OK",
                "message": "Template controls request sent"
            })
        else:
            self.logger.warning("Blender client not connected.")
            # Send error back to the original websocket
            await self.connection_manager.send_message(websocket, {
                "status": "ERROR",
                "message": "Blender client not connected"
            })

    async def handle_template_controls_response(self, websocket: WebSocket, data: Dict[str, Any]):
        """
        Handle the template controls response from Blender and forward to the browser client.
        """
        message_id = data["data"]["message_id"]
        if not message_id:
            self.logger.error("No message_id in template controls response")
            return

        requesting_websocket = self.pending_template_requests.get(message_id)
        if requesting_websocket:
            # Forward the template controls to the browser client
            response = {
                "command": "template_controls",
                "controllables": data["data"]["controllables"]
            }
            await self.connection_manager.send_message(requesting_websocket, response)

            # Clean up the pending request
            del self.pending_template_requests[message_id]
        else:
            self.logger.warning(
                f"No pending request found for message_id: {message_id}")

    async def handle_command_completion(self, websocket: WebSocket, data: Dict[str, Any]):
        """
        Handle the completion of a specific command.

        :param websocket: WebSocket connection
        :param data: Parsed JSON data with completion status
        """
        try:
            message_id = data.get("message_id")
            command = data.get("command", "unknown")

            # Log the completion
            self.logger.info(
                f"Command {command} completed with message ID: {message_id}")

            # Optional: You could implement additional logic here
            # For example:
            # - Update a task status in a database
            # - Trigger a follow-up action
            # - Send a notification to the original requester

            # For video generation, you might want to inform the original requester
            browser_socket = self.connection_manager.connections.get('browser')
            if browser_socket:
                await self.connection_manager.send_message(browser_socket, {
                    "type": "command_completed",
                    "command": command,
                    "message_id": message_id,
                    "status": "success"
                })

        except Exception as e:
            self.logger.error(f"Error handling command completion: {e}")

    async def handle_websocket(self, websocket: WebSocket, client_id: str):
        """
        Main WebSocket connection handler with comprehensive error management.

        :param websocket: Incoming WebSocket connection
        :param client_id: Client identifier
        """
        await websocket.accept()
        self.logger.info(f"Client {client_id} connected")
        self.connection_manager.register_connection(client_id, websocket)

        try:
            while True:
                try:
                    # Wait for and receive a message
                    message = await websocket.receive_text()
                    data = json.loads(message)
                    await self.handle_command(websocket, data)
                except json.JSONDecodeError:
                    self.logger.error(
                        f"Invalid JSON from {client_id}: {message}")
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    self.logger.error(
                        f"Error processing message from {client_id}: {e}")

        except Exception as e:
            self.logger.error(f"Unexpected error in WebSocket handler: {e}")
        finally:
            self.connection_manager.unregister_connection(client_id)
