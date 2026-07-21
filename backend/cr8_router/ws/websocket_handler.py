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


def save_and_upload(save_url, username=None):
    """
    Save the current .blend to disk and upload it to cloud storage via a
    presigned PUT. Shared by the user-triggered `save` command and the emergency
    server-cleanup path.

    A brand-new project (Save As) has no filepath yet, so we save_as to a scratch
    path first; the instance disk is ephemeral, so the cloud upload is the only
    durable copy. Returns (ok: bool, detail: str).

    Must run on Blender's main thread (bpy.ops) — callers are already on it (the
    main-thread command-queue drainer, or a bpy timer callback).
    """
    import bpy

    try:
        filepath = bpy.data.filepath
        if filepath:
            bpy.ops.wm.save_mainfile()
        else:
            uname = username or os.environ.get('CR8_USERNAME') or 'user'
            filepath = f"/tmp/cr8_{uname}.blend"
            bpy.ops.wm.save_as_mainfile(filepath=filepath)
    except Exception as e:
        logging.error(f"Local save failed: {e}")
        return False, f"Local save failed: {e}"

    if not save_url:
        logging.warning("No save URL available — file saved locally only")
        return False, "No cloud save target available"

    try:
        import requests
        with open(filepath, 'rb') as f:
            resp = requests.put(save_url, data=f, timeout=600)
        if resp.status_code == 200:
            logging.info("Uploaded blend file to cloud storage")
            return True, "Saved to cloud"
        logging.error(
            f"Cloud save failed with status {resp.status_code}: {resp.text[:200]}")
        return False, f"Cloud save failed (status {resp.status_code})"
    except Exception as e:
        logging.error(f"Cloud save failed: {e}")
        return False, f"Cloud save failed: {e}"


def upload_file_multipart(filepath, multipart):
    """
    PUT a local file to cloud storage as a sequence of pre-signed part uploads.

    RustFS is reachable from the instance only through the ~100MB-capped tunnel,
    so anything sizeable has to go up in parts, each under the cap. `multipart`
    carries {upload_id, key, part_size, part_urls}, all minted by the engine —
    no credentials ever reach the instance. Returns (ok, {"parts": [...],
    "message": ...}); the engine uses the ETags to complete the upload.

    Generic on purpose: the caller decides what file this is and what to say
    about it on success.
    """
    part_size = multipart.get('part_size')
    part_urls = multipart.get('part_urls') or []
    if not part_size or not part_urls:
        return False, {'message': 'Missing multipart parameters'}

    try:
        import requests
        parts = []
        with open(filepath, 'rb') as f:
            index = 0
            while True:
                chunk = f.read(part_size)
                if not chunk:
                    break
                if index >= len(part_urls):
                    return False, {'message': 'File is larger than the upload can handle'}
                resp = requests.put(part_urls[index], data=chunk, timeout=600)
                if resp.status_code != 200:
                    return False, {
                        'message': f"Part {index + 1} failed (status {resp.status_code})"}
                etag = resp.headers.get('ETag') or resp.headers.get('Etag')
                parts.append({'PartNumber': index + 1, 'ETag': etag})
                index += 1
        if not parts:
            return False, {'message': 'Nothing to upload'}
        logging.info(f"Uploaded {filepath} in {len(parts)} part(s)")
        return True, {'parts': parts}
    except Exception as e:
        logging.error(f"Multipart upload failed: {e}")
        return False, {'message': f"Upload failed: {e}"}


def save_and_upload_multipart(multipart, username=None):
    """
    Save the current .blend and upload it to cloud storage in parts.

    Must run on Blender's main thread (bpy.ops); the command-queue drainer
    already guarantees that. Returns (ok, {"parts": [...], "message": ...}).
    """
    import bpy

    try:
        filepath = bpy.data.filepath
        if filepath:
            bpy.ops.wm.save_mainfile()
        else:
            uname = username or os.environ.get('CR8_USERNAME') or 'user'
            filepath = f"/tmp/cr8_{uname}.blend"
            bpy.ops.wm.save_as_mainfile(filepath=filepath)
    except Exception as e:
        logging.error(f"Local save failed: {e}")
        return False, {'message': f"Local save failed: {e}"}

    ok, result = upload_file_multipart(filepath, multipart)
    if not ok:
        return False, result
    return True, {**result, 'message': 'Saved to cloud'}


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
        # request_timeout=30 overrides the 5s default — Cloudflare/reverse proxies
        # can add latency on the initial polling handshake from VastAI instances.
        self.sio = socketio.Client(
            logger=True,
            engineio_logger=True,
            reconnection=True,
            reconnection_attempts=10,
            reconnection_delay=2,
            reconnection_delay_max=10,
            handle_sigint=False,
            request_timeout=30
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
                transports=['websocket'],
                auth={
                    'token': os.environ.get('CR8_AUTH_TOKEN'),
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
            # Save + upload via the shared helper. The instance disk is scratch —
            # destroyed shortly after we exit — so the cloud PUT is the durable
            # copy. This is the one save path that works while the engine is
            # unreachable (which is exactly why we're in this cleanup), relying on
            # the presigned URL minted at launch.
            save_url = os.environ.get('CR8_SAVE_URL')
            ok, detail = save_and_upload(save_url, username=self.username)
            logging.info(f"Server-cleanup save result: {detail}")

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
