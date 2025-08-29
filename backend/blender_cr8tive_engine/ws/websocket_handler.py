"""
WebSocket handler implementation for Blender AI Router.
This module provides the main WebSocket handler class with command routing to AI addons.
"""

import os
import re
import json
import threading
import logging
import websocket
import time
import bpy
from pathlib import Path
from .utils.session_manager import SessionManager
from .utils.response_manager import ResponseManager

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def execute_in_main_thread(function, args):
    """Execute a function in Blender's main thread"""
    def wrapper():
        function(*args)
        return None
    bpy.app.timers.register(wrapper, first_interval=0.0)


class WebSocketHandler:
    """WebSocket handler with direct command routing."""
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(WebSocketHandler, cls).__new__(cls)
            cls._instance._initialized = False
            cls._instance.lock = threading.Lock()
            # Initialize without connection
            cls._instance.ws = None
            cls._instance.url = None  # Start unconfigured
            cls._instance.username = None
            cls._instance._initialized = True  # Mark as initialized
        return cls._instance

    def __init__(self):
        # Only initialize once
        if hasattr(self, 'processing_complete'):
            return

        # Initialize components
        self.processing_complete = threading.Event()
        self.processed_commands = set()
        self.reconnect_attempts = 0
        self.max_retries = 5
        self.stop_retries = False
        self.ws_thread = None

        logging.info("AI Router WebSocketHandler initialized")

    def initialize_connection(self, url=None):
        """Call this explicitly when ready to connect"""
        if self.ws:
            return  # Already connected

        logging.info(f"WS_URL from env: {os.environ.get('WS_URL')}")
        logging.info(
            f"CR8_USERNAME from env: {os.environ.get('CR8_USERNAME')}")

        # Get URL from environment or argument
        self.url = url or os.environ.get("WS_URL")
        self.username = os.environ.get("CR8_USERNAME")

        if not self.url:
            logging.error("No WS_URL found in environment variables")
            return

        # Fallback to parsing username from URL if not in environment
        if not self.username:
            # Simplified regex for local development
            match = re.match(r'ws://([^:/]+):\d+/ws/([^/]+)/blender', self.url)
            if match:
                self.host = match.group(1)
                self.username = match.group(2)
            else:
                raise ValueError(
                    "Username not found in CR8_USERNAME or WebSocket URL."
                )

        # Set username in SessionManager
        session_manager = SessionManager.get_instance()
        session_manager.set_username(self.username)

        if not self.url:
            raise ValueError(
                "WebSocket URL must be set via WS_URL environment variable "
                "or passed to initialize_connection()"
            )

        # Initialize components only when needed
        self.ws = None

    def connect(self, retries=5, delay=2):
        """Establish WebSocket connection with retries and exponential backoff"""
        self.max_retries = retries
        self.reconnect_attempts = 0
        self.stop_retries = False

        while self.reconnect_attempts < retries and not self.stop_retries:
            try:
                if self.ws:
                    self.ws.close()

                self.ws = websocket.WebSocketApp(
                    self.url,
                    on_message=self._on_message,
                    on_open=self._on_open,
                    on_close=self._on_close,
                    on_error=self._on_error,
                )

                response_manager = ResponseManager.get_instance()
                response_manager.set_websocket(self.ws)

                self.processing_complete.clear()
                self.ws_thread = threading.Thread(
                    target=self._run_websocket, daemon=True
                )
                self.ws_thread.start()

                logging.info(f"WebSocket connection initialized to {self.url}")
                return True
            except Exception as e:
                logging.error(
                    f"Connection to {self.url} failed: {e}, retrying in {delay} seconds..."
                )
                time.sleep(delay)
                delay *= 2
                self.reconnect_attempts += 1

        logging.error(
            f"Max retries reached for {self.url}. Connection failed.")
        return False

    def _run_websocket(self):
        """Run WebSocket without SSL"""
        while not self.processing_complete.is_set() and not self.stop_retries:
            try:
                self.ws.run_forever()
            except websocket.WebSocketException as ws_err:
                logging.error(f"WebSocket error: {ws_err}")
                break
            except Exception as e:
                logging.error(f"Unexpected error in WebSocket connection: {e}")
                break

    def disconnect(self):
        """Disconnect WebSocket"""
        with self.lock:
            self.processing_complete.set()
            self.stop_retries = True
            if self.ws and self.ws.sock and self.ws.sock.connected:
                self.ws.close()
                self.ws = None

            if self.ws_thread:
                self.ws_thread.join(timeout=2)
                self.ws_thread = None

    def _handle_ping(self, data):
        """Handle ping command by responding with a pong"""
        message_id = data.get('message_id')
        response_manager = ResponseManager.get_instance()
        response_manager.send_response(
            "ping_result", True, {"pong": True}, message_id)
        logging.info(f"Responded to ping with message_id: {message_id}")

    def _handle_connection_confirmation(self, data):
        """Handle connection confirmation from CR8 Engine"""
        message_id = data.get('message_id')
        status = data.get('status')
        message = data.get('message')
        logging.info(
            f"Received connection confirmation: status={status}, message={message}")

        # Send registry update to FastAPI when connection is confirmed
        self._send_registry_update()

        # No need to respond, just acknowledge receipt
        if message_id:
            response_manager = ResponseManager.get_instance()
            response_manager.send_response(
                "connection_confirmation_result", True, {"acknowledged": True}, message_id)
            logging.info(
                f"Acknowledged connection confirmation with message_id: {message_id}")

    def _handle_addon_command(self, data):
        """Handle structured addon commands from FastAPI"""
        try:
            addon_id = data.get('addon_id')
            command = data.get('command')
            params = data.get('params', {})
            message_id = data.get('message_id')

            logging.info(
                f"Handling addon command: {addon_id}.{command} with params: {params}")

            # Get router instance
            from .. import get_router
            router = get_router()

            # Execute command through router
            result = router.execute_command(addon_id, command, params)

            # Send response
            response_manager = ResponseManager.get_instance()
            response_manager.send_response(
                f"{command}_result",
                result.get('status') == 'success',
                result,
                message_id
            )

        except Exception as e:
            logging.error(f"Error handling addon command: {str(e)}")
            response_manager = ResponseManager.get_instance()
            response_manager.send_response(
                f"{command}_result",
                False,
                {
                    "status": "error",
                    "message": f"Command handling failed: {str(e)}",
                    "error_code": "COMMAND_HANDLING_ERROR"
                },
                data.get('message_id')
            )

    def _route_command_to_addon(self, command, data):
        """Route legacy commands through the AI router"""
        try:
            # Extract parameters from data
            params = {k: v for k, v in data.items() if k not in [
                'command', 'message_id']}
            message_id = data.get('message_id')

            logging.info(
                f"Routing legacy command: {command} with params: {params}")

            # Get router instance
            from .. import get_router
            router = get_router()

            # Route command to appropriate addon
            result = router.route_command(command, params)

            # Send response
            response_manager = ResponseManager.get_instance()
            response_manager.send_response(
                f"{command}_result",
                result.get('status') == 'success',
                result,
                message_id
            )

        except Exception as e:
            logging.error(f"Error routing command to addon: {str(e)}")
            response_manager = ResponseManager.get_instance()
            response_manager.send_response(
                f"{command}_result",
                False,
                {
                    "status": "error",
                    "message": f"Command routing failed: {str(e)}",
                    "error_code": "ROUTING_ERROR"
                },
                data.get('message_id')
            )

    def _send_registry_update(self):
        """Send registry update event to FastAPI"""
        try:
            from .. import get_registry
            registry = get_registry()

            available_tools = registry.get_available_tools()
            total_addons = len(registry.get_registered_addons())

            registry_event = {
                "type": "registry_updated",
                "total_addons": total_addons,
                "available_tools": available_tools
            }

            if self.ws:
                self.ws.send(json.dumps(registry_event))
                logging.info(
                    f"Sent registry update to FastAPI: {total_addons} addons, {len(available_tools)} tools")
                logging.debug(f"Registry data: {registry_event}")

        except Exception as e:
            logging.error(f"Error sending registry update: {str(e)}")
            import traceback
            traceback.print_exc()

    def _on_open(self, ws):
        self.reconnect_attempts = 0

        def send_init_message():
            try:
                # Use proper format for initialization message
                init_message = json.dumps({
                    'command': 'connection_status',
                    'status': 'Connected',  # Capital C to match what CR8 Engine expects
                    'message': 'Blender registered'
                })
                ws.send(init_message)
                logging.info("Connected Successfully")
            except Exception as e:
                logging.error(f"Error in _on_open: {e}")

        execute_in_main_thread(send_init_message, ())

    def _on_message(self, ws, message):
        self.process_message(message)

    def process_message(self, message):
        try:
            logging.info(f"Processing incoming message: {message}")
            data = json.loads(message)
            command = data.get('command')
            message_id = data.get('message_id')

            logging.info(
                f"Parsed message - command: {command}, message_id: {message_id}")

            # Prevent reprocessing of the same command
            if (command, message_id) in self.processed_commands:
                logging.warning(
                    f"Skipping already processed command: {command} with message_id: {message_id}")
                return

            if not command:
                logging.warning(
                    f"Received message without a valid command: {data}")
                return

            logging.info(f"Looking for handler for command: {command}")

            # Handle utility commands directly
            if command == 'ping':
                def execute_ping():
                    self._handle_ping(data)
                    self.processed_commands.add((command, message_id))
                execute_in_main_thread(execute_ping, ())
                return

            elif command == 'connection_confirmation':
                def execute_confirmation():
                    self._handle_connection_confirmation(data)
                    self.processed_commands.add((command, message_id))
                execute_in_main_thread(execute_confirmation, ())
                return

            # Handle addon commands through router
            elif command.startswith('addon_command'):
                def execute_addon_command():
                    self._handle_addon_command(data)
                    self.processed_commands.add((command, message_id))
                execute_in_main_thread(execute_addon_command, ())
                return

            # Route all other commands through the AI router
            def execute_router_command():
                self._route_command_to_addon(command, data)
                self.processed_commands.add((command, message_id))
                logging.info(
                    f"Marked command {command} with message_id {message_id} as processed")
            execute_in_main_thread(execute_router_command, ())

        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON message: {e}")
        except Exception as e:
            logging.error(f"Error processing WebSocket message: {e}")
            import traceback
            traceback.print_exc()

    def _on_close(self, ws, close_status_code, close_msg):
        logging.info(
            f"WebSocket connection closed. Status: {close_status_code}, Message: {close_msg}")
        self.processing_complete.set()

    def _on_error(self, ws, error):
        logging.error(f"WebSocket error: {error}")
        self.reconnect_attempts += 1
        if self.reconnect_attempts >= self.max_retries:
            logging.error("Max retries reached. Stopping WebSocket attempts.")
            self.stop_retries = True
            self.processing_complete.set()

    def send_response(self, command, result, data=None, message_id=None):
        """
        Send a WebSocket response using ResponseManager.
        This method is kept for compatibility during transition.
        """
        response_manager = ResponseManager.get_instance()
        return response_manager.send_response(command, result, data, message_id)


# Create a singleton instance for use in Blender
def get_handler():
    """Get the singleton WebSocketHandler instance."""
    return WebSocketHandler()


# Register the operator for Blender
class ConnectWebSocketOperator(bpy.types.Operator):
    bl_idname = "ws_handler.connect_websocket"
    bl_label = "Connect WebSocket"
    bl_description = "Initialize WebSocket connection to Cr8tive Engine server"

    def execute(self, context):
        try:
            handler = get_handler()
            handler.initialize_connection()  # Initialize before connecting
            if handler.connect():
                self.report({'INFO'}, f"Connected to {handler.url}")
                return {'FINISHED'}
            else:
                self.report({'ERROR'}, "Connection failed")
        except Exception as e:
            self.report({'ERROR'}, str(e))
        return {'CANCELLED'}


def register():
    """Register WebSocket handler and operator"""
    bpy.utils.register_class(ConnectWebSocketOperator)


def unregister():
    """Unregister WebSocket handler and operator"""
    bpy.utils.unregister_class(ConnectWebSocketOperator)
    handler = get_handler()
    handler.disconnect()
