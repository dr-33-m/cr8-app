"""
Socket.IO handler implementation for Blender AI Router.
This module provides the main Socket.IO handler class with command routing to AI addons.
"""

import os
import re
import json
import logging
import time
import bpy
from pathlib import Path
import socketio
from .utils.session_manager import SessionManager
from .utils.response_manager import ResponseManager
from .message_types import MessageType

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def execute_in_main_thread(function, args):
    """Execute a function in Blender's main thread"""
    def wrapper():
        function(*args)
        return None
    bpy.app.timers.register(wrapper, first_interval=0.0)


class WebSocketHandler:
    """Socket.IO handler with direct command routing."""
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(WebSocketHandler, cls).__new__(cls)
            cls._instance._initialized = False
            cls._instance.lock = __import__('threading').Lock()
            # Initialize without connection
            cls._instance.sio = None
            cls._instance.url = None  # Start unconfigured
            cls._instance.username = None
            cls._instance._initialized = True  # Mark as initialized
        return cls._instance

    def __init__(self):
        # Only initialize once
        if hasattr(self, 'processing_complete'):
            return

        # Initialize components
        self.processing_complete = __import__('threading').Event()
        self.processed_commands = set()
        self.processing_commands = set()  # Track in-progress commands
        self.stop_retries = False

        logging.info("AI Router Socket.IO Handler initialized")

    def initialize_connection(self, url=None):
        """Call this explicitly when ready to connect"""
        if self.sio:
            return  # Already initialized

        logging.info(f"WS_URL from env: {os.environ.get('WS_URL')}")
        logging.info(
            f"CR8_USERNAME from env: {os.environ.get('CR8_USERNAME')}")

        # Get URL from environment or argument
        self.url = url or os.environ.get("WS_URL")
        self.username = os.environ.get("CR8_USERNAME")

        if not self.url:
            logging.error("No WS_URL found in environment variables")
            return

        # Username is required and must come from CR8_USERNAME environment variable
        if not self.username:
            raise ValueError(
                "Username required: Set CR8_USERNAME environment variable"
            )

        # Set username in SessionManager
        session_manager = SessionManager.get_instance()
        session_manager.set_username(self.username)

        if not self.url:
            raise ValueError(
                "WebSocket URL must be set via WS_URL environment variable "
                "or passed to initialize_connection()"
            )

        # Create Socket.IO client
        self.sio = socketio.Client(
            logger=True,
            engineio_logger=True,
            reconnection=True,
            reconnection_attempts=5,
            reconnection_delay=2,
            reconnection_delay_max=10
        )

        # Register event handlers
        self._register_handlers()

    def _register_handlers(self):
        """Register all Socket.IO event handlers"""

        @self.sio.on('connect', namespace='/blender')
        def on_connect():
            logging.info("Connected to Socket.IO server")
            self.processing_complete.clear()

            def send_init_message():
                try:
                    # Send connection status via Socket.IO emit
                    self.sio.emit(
                        'connection_status',
                        {
                            'status': 'Connected',
                            'message': 'Blender registered'
                        },
                        namespace='/blender'
                    )
                    logging.info("Sent connection status to server")

                    # Send registry update
                    self._send_registry_update()
                except Exception as e:
                    logging.error(f"Error in on_connect: {e}")

            execute_in_main_thread(send_init_message, ())

        @self.sio.on('disconnect', namespace='/blender')
        def on_disconnect(reason):
            logging.info(f"Disconnected from server: {reason}")
            self.processing_complete.set()
            self.processing_commands.clear()

        @self.sio.on('connect_error', namespace='/blender')
        def on_connect_error(data):
            logging.error(f"Connection error: {data}")

        @self.sio.on(MessageType.COMMAND_RECEIVED, namespace='/blender')
        def on_command_received(data):
            """Handle commands forwarded from backend (standardized)"""
            logging.info(f"Received {MessageType.COMMAND_RECEIVED}: {data}")

            def execute():
                self.process_message(data)

            execute_in_main_thread(execute, ())

        @self.sio.on('ping', namespace='/blender')
        def on_ping(data):
            """Handle ping events"""
            logging.info(f"Received ping: {data}")

            def execute():
                self._handle_ping(data)

            execute_in_main_thread(execute, ())

    def connect(self, retries=5, delay=2):
        """Establish Socket.IO connection"""
        try:
            # Use URL directly (should be http:// or https://)
            connection_url = self.url

            logging.info(f"Connecting to Socket.IO server at {connection_url}")

            self.sio.connect(
                connection_url,
                namespaces=['/blender'],
                socketio_path='/ws/socket.io/',
                auth={
                    'username': self.username,
                    'blend_file_path': bpy.data.filepath
                },
                wait=False  # Non-blocking, Socket.IO handles threading
            )

            # Set ResponseManager's socketio client
            response_manager = ResponseManager.get_instance()
            response_manager.set_socketio(self.sio)

            logging.info(f"Socket.IO connection initialized to {connection_url}")
            return True

        except Exception as e:
            logging.error(f"Connection to {connection_url} failed: {e}")
            return False

    def disconnect(self):
        """Disconnect Socket.IO"""
        with self.lock:
            self.processing_complete.set()
            self.stop_retries = True
            try:
                if self.sio and self.sio.connected:
                    self.sio.disconnect()
                    self.sio = None
            except Exception as e:
                logging.error(f"Error disconnecting: {e}")

            self.processing_commands.clear()
            self.processed_commands.clear()

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
        """Handle structured addon commands with route preservation"""
        try:
            addon_id = data.get('addon_id')
            command = data.get('command')
            params = data.get('params', {})
            message_id = data.get('message_id')
            
            # Extract route from incoming command (critical for proper response routing)
            # Check both metadata.route and direct route field for compatibility
            route = 'direct'  # Default
            if 'metadata' in data:
                route = data['metadata'].get('route', 'direct')
            elif 'route' in data:
                route = data.get('route', 'direct')

            logging.info(
                f"Handling addon command: {addon_id}.{command} with params: {params}, route: {route}")

            # Get router instance
            from .. import get_router
            router = get_router()

            # Execute command through router
            result = router.execute_command(addon_id, command, params)

            # Send response with preserved route
            response_manager = ResponseManager.get_instance()
            response_manager.send_response(
                f"{command}_result",
                result.get('status') == 'success',
                result,
                message_id,
                route=route  # Preserve route for proper forwarding
            )

        except Exception as e:
            logging.error(f"Error handling addon command: {str(e)}")
            response_manager = ResponseManager.get_instance()
            
            # Extract route for error response too
            route = 'direct'
            if 'metadata' in data:
                route = data['metadata'].get('route', 'direct')
            elif 'route' in data:
                route = data.get('route', 'direct')
                
            response_manager.send_response(
                f"{command}_result",
                False,
                {
                    "status": "error",
                    "message": f"Command handling failed: {str(e)}",
                    "error_code": "COMMAND_HANDLING_ERROR"
                },
                data.get('message_id'),
                route=route
            )

    def _route_command_to_addon(self, command, data):
        """Route commands through the AI router using structured format"""
        try:
            # Extract parameters from structured format only
            params = data.get('params', {})
            addon_id = data.get('addon_id')
            message_id = data.get('message_id')

            logging.info(
                f"Routing command: {command} with params: {params}, addon_id: {addon_id}")

            # Get router instance
            from .. import get_router
            router = get_router()

            # Route command to appropriate addon (with addon_id if available)
            if addon_id:
                result = router.execute_command(addon_id, command, params)
            else:
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
        """Send registry update event to FastAPI via Socket.IO"""
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

            if self.sio and self.sio.connected:
                self.sio.emit('registry_update', registry_event, namespace='/blender')
                logging.info(
                    f"Sent registry update to server: {total_addons} addons, {len(available_tools)} tools")
                logging.debug(f"Registry data: {registry_event}")

        except Exception as e:
            logging.error(f"Error sending registry update: {str(e)}")
            import traceback
            traceback.print_exc()

    def process_message(self, data):
        """Process incoming message with deduplication"""
        try:
            logging.info(f"Processing incoming message: {data}")
            
            # Get both type and command fields
            message_type = data.get('type')
            command = data.get('command')
            message_id = data.get('message_id')

            logging.info(
                f"Parsed message - type: {message_type}, command: {command}, message_id: {message_id}")

            # Create unique command key using type or command
            command_identifier = message_type or command
            command_key = (command_identifier, message_id) if message_id else None

            # Validation safety net: warn about missing message IDs for important commands
            if not message_id and command_identifier not in ['ping', 'connection_confirmation']:
                logging.warning(
                    f"Command {command_identifier} received without message_id - this may cause deduplication issues")

            # Check if already processed
            if command_key and command_key in self.processed_commands:
                logging.warning(
                    f"Skipping already processed command: {command_identifier} with message_id: {message_id}")
                return

            # Check if currently processing (CRITICAL: prevents duplicate execution)
            if command_key and command_key in self.processing_commands:
                logging.warning(
                    f"Command {command_identifier} with message_id {message_id} still processing, ignoring duplicate")
                return

            # Mark as processing
            if command_key:
                self.processing_commands.add(command_key)

            if not command_identifier:
                logging.warning(
                    f"Received message without a valid type or command: {data}")
                return

            logging.info(f"Looking for handler for type: {message_type}, command: {command}")

            # Route based on message type first, then command
            if message_type == 'addon_command':
                # Handle addon commands through router (AI-routed commands)
                self._handle_addon_command(data)
                
            elif command == 'ping':
                # Handle utility commands directly
                self._handle_ping(data)

            elif command == 'connection_confirmation':
                self._handle_connection_confirmation(data)

            elif command:
                # Route all other commands through the AI router (direct commands)
                self._route_command_to_addon(command, data)
            
            else:
                logging.warning(f"Unknown message type/command: type={message_type}, command={command}")

            # Mark as processed and remove from processing
            if command_key:
                self.processing_commands.discard(command_key)
                self.processed_commands.add(command_key)
                logging.info(
                    f"Marked command {command_identifier} with message_id {message_id} as processed")

        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON message: {e}")
        except Exception as e:
            logging.error(f"Error processing message: {e}")
            import traceback
            traceback.print_exc()
            # Ensure we remove from processing on error
            if command_key and command_key in self.processing_commands:
                self.processing_commands.discard(command_key)

    def send_response(self, command, result, data=None, message_id=None):
        """
        Send a Socket.IO response using ResponseManager.
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
    bl_label = "Connect Socket.IO"
    bl_description = "Initialize Socket.IO connection to Cr8tive Engine server"

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
    """Register Socket.IO handler and operator"""
    bpy.utils.register_class(ConnectWebSocketOperator)


def unregister():
    """Unregister Socket.IO handler and operator"""
    bpy.utils.unregister_class(ConnectWebSocketOperator)
    handler = get_handler()
    handler.disconnect()
