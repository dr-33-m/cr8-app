"""
WebSocket handler implementation for blender_cr8tive_engine.
This module provides the main WebSocket handler class with direct command routing.
"""

import os
import re
import json
import threading
import logging
import websocket
import ssl
import time
import bpy
from pathlib import Path
from ..templates.template_wizard import TemplateWizard
from ..core.blender_controllers import BlenderControllers
from ..assets.asset_placer import AssetPlacer
from .utils.session_manager import SessionManager
from .utils.response_manager import ResponseManager

# Import handler classes
from .handlers.animation import AnimationHandlers
from .handlers.asset import AssetHandlers
from .handlers.render import RenderHandlers
from .handlers.scene import SceneHandlers
from .handlers.template import TemplateHandlers
from .handlers.camera import CameraHandlers
from .handlers.light import LightHandlers
from .handlers.material import MaterialHandlers
from .handlers.object import ObjectHandlers

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
        if hasattr(self, 'command_handlers'):
            return

        # Initialize components
        self.command_handlers = {}
        self.processing_complete = threading.Event()
        self.processed_commands = set()
        self.reconnect_attempts = 0
        self.max_retries = 5
        self.stop_retries = False
        self.ws_thread = None

        # Register command handlers directly
        self._register_command_handlers()

        logging.info(
            f"WebSocketHandler initialized with {len(self.command_handlers)} command handlers")

    def _register_command_handlers(self):
        """Register all command handlers directly."""
        # Utility commands
        self.command_handlers.update({
            'ping': self._handle_ping,
            'connection_confirmation': self._handle_connection_confirmation,
        })

        # Animation commands
        self.command_handlers.update({
            'load_camera_animation': AnimationHandlers.handle_load_camera_animation,
            'load_light_animation': AnimationHandlers.handle_load_light_animation,
            'load_product_animation': AnimationHandlers.handle_load_product_animation,
        })

        # Asset commands
        self.command_handlers.update({
            'append_asset': AssetHandlers.handle_append_asset,
            'remove_assets': AssetHandlers.handle_remove_assets,
            'swap_assets': AssetHandlers.handle_swap_assets,
            'rotate_assets': AssetHandlers.handle_rotate_assets,
            'scale_assets': AssetHandlers.handle_scale_assets,
            'get_asset_info': AssetHandlers.handle_get_asset_info,
        })

        # Scene commands - using dedicated handlers instead of SceneHandlers
        self.command_handlers.update({
            'update_camera': CameraHandlers.handle_update_camera,
            'update_light': LightHandlers.handle_update_light,
            'update_material': MaterialHandlers.handle_update_material,
            'update_object': ObjectHandlers.handle_update_object,

            # Keep legacy handlers for backward compatibility
            'change_camera': SceneHandlers.handle_camera_change,
        })

        # Rendering commands
        self.command_handlers.update({
            'start_preview_rendering': RenderHandlers.handle_preview_rendering,
            'generate_video': RenderHandlers.handle_generate_video,
        })

        # Template commands
        self.command_handlers.update({
            'get_template_controls': TemplateHandlers.handle_get_template_controls,
            'update_template_control': TemplateHandlers.handle_update_template_control,
            'get_template_info': TemplateHandlers.handle_get_template_info,
        })

    def initialize_connection(self, url=None):
        """Call this explicitly when ready to connect"""
        if self.ws:
            return  # Already connected

        # Get URL from environment or argument
        self.url = url or os.environ.get("WS_URL")

        # Updated regex to handle both 'ws' and 'wss', local IPs, localhost, and production domains
        match = re.match(
            r'ws[s]?://([^:/]+)(?::\d+)?/ws/([^/]+)/blender', self.url)
        if match:
            # Extract host (local IP, localhost, or production domain)
            self.host = match.group(1)
            self.username = match.group(2)  # Extract username

            # Set username in SessionManager
            session_manager = SessionManager.get_instance()
            session_manager.set_username(self.username)
        else:
            raise ValueError(
                "Invalid WebSocket URL format. Unable to extract username."
            )

        if not self.url:
            raise ValueError(
                "WebSocket URL must be set via WS_URL environment variable "
                "or passed to initialize_connection()"
            )

        # Initialize components only when needed
        self.ws = None
        self.wizard = TemplateWizard()
        self.controllers = BlenderControllers()
        self.asset_placer = AssetPlacer()  # Initialize the asset placer

    def connect(self, retries=5, delay=2):
        """Establish WebSocket connection with retries and exponential backoff"""
        self.max_retries = retries
        self.reconnect_attempts = 0
        self.stop_retries = False

        try:
            # Create SSL context with proper security settings
            ssl_context = ssl.create_default_context(
                purpose=ssl.Purpose.SERVER_AUTH,
                cafile="/home/thamsanqa/cloudflare_cert.crt"
            )
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_REQUIRED

            # Verify the SSL context is properly configured
            logging.info(
                "SSL Context created with: verify_mode=CERT_REQUIRED, check_hostname=False")
        except Exception as ssl_error:
            logging.error(f"Failed to create SSL context: {ssl_error}")
            return False

        while self.reconnect_attempts < retries and not self.stop_retries:
            try:
                if self.ws:
                    self.ws.close()

                # Use the environment-configured URL with SSL options
                self.ws = websocket.WebSocketApp(
                    self.url,
                    on_message=self._on_message,
                    on_open=self._on_open,
                    on_close=self._on_close,
                    on_error=self._on_error,
                )

                # Set WebSocket in ResponseManager
                response_manager = ResponseManager.get_instance()
                response_manager.set_websocket(self.ws)

                self.processing_complete.clear()
                self.ws_thread = threading.Thread(
                    target=lambda: self._run_websocket(ssl_context),
                    daemon=True
                )
                self.ws_thread.start()

                logging.info(f"WebSocket connection initialized to {self.url}")
                return True
            except Exception as e:
                logging.error(
                    f"Connection to {self.url} failed: {e}, retrying in {delay} seconds..."
                )
                time.sleep(delay)
                delay *= 2  # Exponential backoff
                self.reconnect_attempts += 1

        logging.error(
            f"Max retries reached for {self.url}. Connection failed.")
        return False

    def _run_websocket(self, ssl_context):
        """Run WebSocket with SSL context"""
        while not self.processing_complete.is_set() and not self.stop_retries:
            try:
                self.ws.run_forever(
                    sslopt={
                        "cert_reqs": ssl_context.verify_mode,
                        "check_hostname": ssl_context.check_hostname,
                        "ssl_context": ssl_context
                    }
                )
            except ssl.SSLError as ssl_err:
                logging.error(f"SSL Error in WebSocket connection: {ssl_err}")
                self.stop_retries = True
                break
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

        # No need to respond, just acknowledge receipt
        if message_id:
            response_manager = ResponseManager.get_instance()
            response_manager.send_response(
                "connection_confirmation_result", True, {"acknowledged": True}, message_id)
            logging.info(
                f"Acknowledged connection confirmation with message_id: {message_id}")

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

            # Get handler from registered handlers
            handler_method = self.command_handlers.get(command)

            if handler_method:
                logging.info(
                    f"Found handler for command {command}: {handler_method.__name__ if hasattr(handler_method, '__name__') else 'anonymous'}")

                def execute_handler():
                    handler_method(data)
                    # Mark this command as processed
                    self.processed_commands.add((command, message_id))
                    logging.info(
                        f"Marked command {command} with message_id {message_id} as processed")
                execute_in_main_thread(execute_handler, ())
            else:
                logging.warning(f"No handler found for command: {command}")

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
