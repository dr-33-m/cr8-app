import os
import bpy
import re
import json
import threading
import logging
import websocket
from .template_wizard import TemplateWizard
from .blender_controllers import BlenderControllers
from .video_generator import GenerateVideo
from .asset_placer import AssetPlacer
import tempfile
from pathlib import Path
import ssl
import time  # Add this if not already imported

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def execute_in_main_thread(function, args):
    """Execute a function in Blender's main thread"""
    def wrapper():
        function(*args)
        return None
    bpy.app.timers.register(wrapper, first_interval=0.0)


class WebSocketHandler:
    _instance = None

    # Define the dispatch table mapping commands to handler functions
    command_handlers = {
        'change_camera': '_handle_camera_change',
        'update_light': '_handle_light_update',
        'update_material': '_handle_material_update',
        'update_object': '_handle_object_transformation',
        'start_preview_rendering': '_handle_preview_rendering',
        'generate_video': '_handle_generate_video',
        'rescan_template': '_handle_rescan_template',
        # Asset Placer commands
        'append_asset': '_handle_append_asset',
        'remove_assets': '_handle_remove_assets',
        'swap_assets': '_handle_swap_assets',
        'rotate_assets': '_handle_rotate_assets',
        'scale_assets': '_handle_scale_assets',
        'get_asset_info': '_handle_get_asset_info'
    }

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
        # Empty __init__ since we handle initialization in __new__
        pass

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
        self.processing_complete = threading.Event()
        self.processed_commands = set()
        self.reconnect_attempts = 0
        self.max_retries = 5
        self.stop_retries = False

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

    def _on_open(self, ws):
        self.reconnect_attempts = 0

        def send_init_message():
            try:
                init_message = json.dumps({
                    'status': 'Connected',
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

            # Optional: Add a retry limit or cooling period
            handler_method = getattr(
                self, self.command_handlers.get(command), None)

            if handler_method:
                logging.info(
                    f"Found handler for command {command}: {handler_method.__name__}")

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

            # Optional: Disconnect or reset to prevent further processing
            self.disconnect()

    def _handle_camera_change(self, data):
        result = self.controllers.set_active_camera(data.get('camera_name'))
        self._send_response('camera_change_result', result)

    def _handle_light_update(self, data):
        result = self.controllers.update_light(
            data.get('light_name'), color=data.get('color'), strength=data.get('strength'))
        self._send_response('light_update_result', result)

    def _handle_material_update(self, data):
        result = self.controllers.update_material(
            data.get('material_name'),
            color=data.get('color'),
            roughness=data.get('roughness'),
            metallic=data.get('metallic')
        )
        self._send_response('material_update_result', result)

    def _handle_object_transformation(self, data):
        result = self.controllers.update_object(
            data.get('object_name'), location=data.get('location'), rotation=data.get('rotation'), scale=data.get('scale'))
        self._send_response('object_transformation_result', result)

    def _handle_preview_rendering(self, data):
        logging.info("Starting preview rendering")
        params = data.get('params', {})
        preview_renderer = self.controllers.create_preview_renderer(
            self.username)

        try:
            # Process updates before rendering
            if 'camera' in params:
                camera_data = params['camera']
                result = self.controllers.set_active_camera(
                    camera_data.get('camera_name'))
                logging.info(f"Camera update result: {result}")

            if 'lights' in params:
                light_update = params['lights']
                result = self.controllers.update_light(
                    light_update.get('light_name'),
                    color=light_update.get('color'),
                    strength=light_update.get('strength')
                )
                logging.info(f"Light update result: {result}")

            if 'materials' in params:
                for material_update in params['materials']:
                    result = self.controllers.update_material(
                        material_update.get('material_name'),
                        color=material_update.get('color'),
                        roughness=material_update.get('roughness'),
                        metallic=material_update.get('metallic')
                    )
                    logging.info(f"Material update result: {result}")

            if 'objects' in params:
                for object_update in params['objects']:
                    result = self.controllers.update_object(
                        object_update.get('object_name'),
                        location=object_update.get('location'),
                        rotation=object_update.get('rotation'),
                        scale=object_update.get('scale')
                    )
                    logging.info(f"Object update result: {result}")

            # Cleanup any existing preview frames
            preview_renderer.cleanup()

            # Setup preview render settings
            preview_renderer.setup_preview_render(params)

            # Render the entire animation once
            bpy.ops.render.opengl(animation=True)

            self._send_response('start_broadcast', True)

        except Exception as e:
            logging.error(f"Preview rendering error: {e}")
            import traceback
            traceback.print_exc()
            self._send_response('Preview Rendering failed', False)

    def _handle_generate_video(self, data):
        """Generate video based on the available frames."""
        image_sequence_directory = Path(
            f"/mnt/shared_storage/Cr8tive_Engine/Sessions/{self.username}") / "preview"
        output_file = image_sequence_directory / "preview.mp4"
        resolution = (1280, 720)
        fps = 30

        try:

            # Include the message_id in your processing and response
            message_id = data.get('message_id')

            # Ensure the directory exists
            image_sequence_directory.mkdir(parents=True, exist_ok=True)

            # Check if there are actually image files in the directory
            image_files = list(image_sequence_directory.glob('*.png'))
            if not image_files:
                raise ValueError(
                    "No image files found in the specified directory")

            # Initialize and execute the handler
            video_generator = GenerateVideo(
                str(image_sequence_directory),
                str(output_file),
                resolution,
                fps
            )
            video_generator.gen_video_from_images()

            # Send success response with message_id
            self._send_response('generate_video', {
                "success": True,
                "status": "completed",
                "message_id": message_id
            })

            # Disconnect from the client if everything is successful
            self.disconnect()

        except Exception as e:
            error_message = str(e)
            logging.error(
                f"Video generation error in directory {image_sequence_directory}: {error_message}"
            )
            import traceback
            traceback.print_exc()

            # Send error response with message_id
            self._send_response('generate_video', {
                "success": False,
                "status": "failed",
                "message_id": message_id
            })

            logging.error(f"Video generation failed: {e}")

    def _handle_rescan_template(self, data):
        """Rescan the controllable objects and send the response"""
        try:
            message_id = data.get('message_id')
            logging.info(
                f"Handling template rescan request with message_id: {message_id}")

            controllables = self.wizard.scan_controllable_objects()
            logging.info(f"Scanned {len(controllables)} controllable objects")

            # Format the response with message_id and data
            result = {
                "data": {
                    "controllables": controllables,
                    "message_id": message_id  # Include in data object
                }
            }
            logging.info(
                f"Sending template controls response with message_id: {message_id}")
            self._send_response('template_controls', True, result)
            logging.info(
                f"Successfully rescanned template with {len(controllables)} controllables")
        except Exception as e:
            logging.error(f"Error during template rescan: {e}")
            self._send_response('template_controls', False, {
                "message": str(e),
                "message_id": data.get('message_id')
            })

    def _handle_append_asset(self, data):
        """Handle appending an asset to an empty"""
        try:
            message_id = data.get('message_id')
            logging.info(
                f"Handling append asset request with message_id: {message_id}")

            # Extract parameters from the request
            empty_name = data.get('empty_name')
            filepath = data.get('filepath')
            asset_name = data.get('asset_name')
            mode = data.get('mode', 'PLACE')
            scale_factor = data.get('scale_factor', 1.0)
            center_origin = data.get('center_origin', False)

            # Call the asset placer to append the asset
            result = self.asset_placer.append_asset(
                empty_name,
                filepath,
                asset_name,
                mode=mode,
                scale_factor=scale_factor,
                center_origin=center_origin
            )

            logging.info(f"Asset append result: {result}")

            # Send response with the result
            self._send_response('append_asset_result', result.get('success', False), {
                "data": result,
                "message_id": message_id
            })

        except Exception as e:
            logging.error(f"Error during asset append: {e}")
            import traceback
            traceback.print_exc()
            self._send_response('append_asset_result', False, {
                "message": str(e),
                "message_id": data.get('message_id')
            })

    def _handle_remove_assets(self, data):
        """Handle removing assets from an empty"""
        try:
            message_id = data.get('message_id')
            logging.info(
                f"Handling remove assets request with message_id: {message_id}")

            # Extract parameters from the request
            empty_name = data.get('empty_name')

            # Call the asset placer to remove the assets
            result = self.asset_placer.remove_assets(empty_name)

            logging.info(f"Asset removal result: {result}")

            # Send response with the result
            self._send_response('remove_assets_result', result.get('success', False), {
                "data": result,
                "message_id": message_id
            })

        except Exception as e:
            logging.error(f"Error during asset removal: {e}")
            import traceback
            traceback.print_exc()
            self._send_response('remove_assets_result', False, {
                "message": str(e),
                "message_id": data.get('message_id')
            })

    def _handle_swap_assets(self, data):
        """Handle swapping assets between two empties"""
        try:
            message_id = data.get('message_id')
            logging.info(
                f"Handling swap assets request with message_id: {message_id}")

            # Extract parameters from the request
            empty1_name = data.get('empty1_name')
            empty2_name = data.get('empty2_name')

            # Call the asset placer to swap the assets
            result = self.asset_placer.swap_assets(empty1_name, empty2_name)

            logging.info(f"Asset swap result: {result}")

            # Send response with the result
            self._send_response('swap_assets_result', result.get('success', False), {
                "data": result,
                "message_id": message_id
            })

        except Exception as e:
            logging.error(f"Error during asset swap: {e}")
            import traceback
            traceback.print_exc()
            self._send_response('swap_assets_result', False, {
                "message": str(e),
                "message_id": data.get('message_id')
            })

    def _handle_rotate_assets(self, data):
        """Handle rotating assets on an empty"""
        try:
            message_id = data.get('message_id')
            logging.info(
                f"Handling rotate assets request with message_id: {message_id}")

            # Extract parameters from the request
            empty_name = data.get('empty_name')
            degrees = data.get('degrees')
            reset = data.get('reset', False)

            # Call the asset placer to rotate the assets
            result = self.asset_placer.rotate_assets(
                empty_name, degrees, reset)

            logging.info(f"Asset rotation result: {result}")

            # Send response with the result
            self._send_response('rotate_assets_result', result.get('success', False), {
                "data": result,
                "message_id": message_id
            })

        except Exception as e:
            logging.error(f"Error during asset rotation: {e}")
            import traceback
            traceback.print_exc()
            self._send_response('rotate_assets_result', False, {
                "message": str(e),
                "message_id": data.get('message_id')
            })

    def _handle_scale_assets(self, data):
        """Handle scaling assets on an empty"""
        try:
            message_id = data.get('message_id')
            logging.info(
                f"Handling scale assets request with message_id: {message_id}")

            # Extract parameters from the request
            empty_name = data.get('empty_name')
            scale_percent = data.get('scale_percent')
            reset = data.get('reset', False)

            # Call the asset placer to scale the assets
            result = self.asset_placer.scale_assets(
                empty_name, scale_percent, reset)

            logging.info(f"Asset scaling result: {result}")

            # Send response with the result
            self._send_response('scale_assets_result', result.get('success', False), {
                "data": result,
                "message_id": message_id
            })

        except Exception as e:
            logging.error(f"Error during asset scaling: {e}")
            import traceback
            traceback.print_exc()
            self._send_response('scale_assets_result', False, {
                "message": str(e),
                "message_id": data.get('message_id')
            })

    def _handle_get_asset_info(self, data):
        """Handle getting information about assets on an empty"""
        try:
            message_id = data.get('message_id')
            logging.info(
                f"Handling get asset info request with message_id: {message_id}")

            # Extract parameters from the request
            empty_name = data.get('empty_name')

            # Call the asset placer to get the asset info
            result = self.asset_placer.get_asset_info(empty_name)

            logging.info(f"Asset info result: {result}")

            # Send response with the result
            self._send_response('asset_info_result', result.get('success', False), {
                "data": result,
                "message_id": message_id
            })

        except Exception as e:
            logging.error(f"Error during get asset info: {e}")
            import traceback
            traceback.print_exc()
            self._send_response('asset_info_result', False, {
                "message": str(e),
                "message_id": data.get('message_id')
            })

    def _send_response(self, command, result, data=None, message_id=None):
        """
        Send a WebSocket response.

        :param command: The command to send (e.g., 'template_controls')
        :param result: Boolean indicating success or failure
        :param data: Optional additional data to send (e.g., controllables object)
        :param message_id: Optional message ID for tracking requests
        """
        logging.info(f"Preparing response for command: {command}")
        status = 'success' if result else 'failed'

        response = {
            'command': command,
            'status': status
        }

        # Include the data in the response if provided
        if data is not None:
            # Extract message_id if present in data
            if isinstance(data, dict) and 'message_id' in data:
                response['message_id'] = data['message_id']
            elif isinstance(data, dict) and 'data' in data and isinstance(data['data'], dict) and 'message_id' in data['data']:
                response['message_id'] = data['data']['message_id']

            # Always keep data in its own field to maintain structure
            response['data'] = data

        # Convert the response dictionary to a JSON string
        json_response = json.dumps(response)
        logging.info(f"Sending WebSocket response: {json_response}")

        # Send the response via WebSocket
        self.ws.send(json_response)

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


class ConnectWebSocketOperator(bpy.types.Operator):
    bl_idname = "ws_handler.connect_websocket"
    bl_label = "Connect WebSocket"
    bl_description = "Initialize WebSocket connection to Cr8tive Engine server"

    def execute(self, context):
        try:
            handler = WebSocketHandler()
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
    websocket_handler.disconnect()
