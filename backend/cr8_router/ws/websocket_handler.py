"""
Socket.IO handler implementation for Blender AI Router.
This module provides the main Socket.IO handler class with command routing to AI addons.
"""

import os
import logging
import socketio
from .utils.session_manager import SessionManager
from .utils.response_manager import ResponseManager
from .handlers import register_event_handlers, execute_in_main_thread

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


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
        self.server_cleanup_timer = None  # Timer for 5-minute cleanup on disconnect

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
            reconnection_delay_max=10,
            handle_sigint=False
        )

        # Register event handlers
        register_event_handlers(self)

    def connect(self, retries=5, delay=2):
        """Establish Socket.IO connection"""
        try:
            import bpy
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

    def send_response(self, command, result, data=None, message_id=None):
        """
        Send a Socket.IO response using ResponseManager.
        This method is kept for compatibility during transition.
        """
        response_manager = ResponseManager.get_instance()
        return response_manager.send_response(command, result, data, message_id)

    def start_server_cleanup_timer(self):
        """
        Start a 5-minute timer that will save and close Blender if server remains unreachable.
        This is called when Socket.IO disconnects after exhausting retry attempts.
        """
        logging.info("start_server_cleanup_timer() called")
        
        try:
            import bpy
            logging.info("bpy imported successfully")
        except Exception as e:
            logging.error(f"Failed to import bpy: {e}", exc_info=True)
            return
        
        # Cancel any existing timer
        if self.server_cleanup_timer is not None:
            try:
                bpy.app.timers.unregister(self.server_cleanup_timer)
                logging.info("Unregistered existing cleanup timer")
            except Exception as e:
                logging.warning(f"Could not unregister existing timer: {e}")
            self.server_cleanup_timer = None
        
        logging.warning(
            "Server unreachable after 5 connection attempts. "
            "Blender will save and close in 5 minutes if server does not reconnect."
        )
        
        # Create timer function that will be called after 5 minutes (300 seconds)
        def cleanup_timer():
            logging.info("Cleanup timer callback triggered")
            self.perform_server_cleanup()
            return None  # Return None to unregister the timer
        
        try:
            # Register timer to run after 300 seconds
            self.server_cleanup_timer = bpy.app.timers.register(
                cleanup_timer,
                first_interval=300.0
            )
            logging.info("5-minute server cleanup timer registered successfully")
        except Exception as e:
            logging.error(f"Failed to register cleanup timer: {e}", exc_info=True)

    def perform_server_cleanup(self):
        """
        Save the current Blender file and quit Blender gracefully.
        This is called after 5 minutes of server unavailability.
        """
        import bpy
        
        logging.info("Performing server cleanup: saving file and closing Blender")
        
        try:
            # Save the current file
            if bpy.data.filepath:
                logging.info(f"Saving Blender file: {bpy.data.filepath}")
                bpy.ops.wm.save_mainfile()
            else:
                logging.warning("No blend file path found, skipping save")
            
            # Quit Blender
            logging.info("Closing Blender instance")
            bpy.ops.wm.quit_blender()
            
        except Exception as e:
            logging.error(f"Error during server cleanup: {e}")
            # Still try to quit even if save failed
            try:
                bpy.ops.wm.quit_blender()
            except Exception as quit_error:
                logging.error(f"Error quitting Blender: {quit_error}")


# Create a singleton instance for use in Blender
def get_handler():
    """Get the singleton WebSocketHandler instance."""
    return WebSocketHandler()


def register():
    """Register Socket.IO handler and operator"""
    from .handlers import register_blender
    register_blender()


def unregister():
    """Unregister Socket.IO handler and operator"""
    from .handlers import unregister_blender
    unregister_blender()
    handler = get_handler()
    handler.disconnect()
