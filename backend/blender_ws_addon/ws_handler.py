import bpy
import json
import threading
import logging
import websocket
from .template_wizard import TemplateWizard
from .blender_controllers import BlenderControllers

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
        'rescan_template': '_handle_rescan_template'
    }

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(WebSocketHandler, cls).__new__(cls)
            cls._instance._initialized = False
            cls._instance.lock = threading.Lock()
        return cls._instance

    def __init__(self, url="ws://localhost:5001/blender"):
        if self._initialized:
            return

        self.url = url
        self.wizard = TemplateWizard()
        self.controllers = BlenderControllers()

        self.ws = None
        self.ws_thread = None
        self._initialized = True

    def connect(self, retries=5, delay=2):
        """Establish WebSocket connection with retries"""
        attempt = 0
        while attempt < retries:
            try:
                if self.ws:
                    self.ws.close()

                self.ws = websocket.WebSocketApp(
                    self.url,
                    on_message=self._on_message,
                    on_open=self._on_open,
                    on_close=self._on_close,
                    on_error=self._on_error
                )
                self.ws_thread = threading.Thread(
                    target=self.ws.run_forever, daemon=True)
                self.ws_thread.start()

                logging.info("WebSocket connection initialized")
                return True
            except Exception as e:
                logging.error(
                    f"Connection failed: {e}, retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= 2
                attempt += 1
        return False

    def disconnect(self):
        """Disconnect WebSocket"""
        with self.lock:
            if self.ws and self.ws.sock and self.ws.sock.connected:
                self.ws.close()
                self.ws = None

            if self.ws_thread:
                self.ws_thread.join(timeout=2)
                self.ws_thread = None

    def _on_open(self, ws):
        def send_template_controls():
            try:
                controllables = self.wizard.scan_controllable_objects()
                init_message = json.dumps({
                    'command': 'template_controls',
                    'controllables': controllables
                })
                ws.send(init_message)
                logging.info("Sent template controls to server")
            except Exception as e:
                logging.error(f"Error in _on_open: {e}")

        execute_in_main_thread(send_template_controls, ())

    def _on_message(self, ws, message):
        self.process_message(message)

    def process_message(self, message):
        try:
            data = json.loads(message)
            command = data.get('command')

            # Retrieve the handler function from the dispatch table
            handler_method = getattr(
                self, self.command_handlers.get(command), None)

            if handler_method:
                def execute_handler():
                    # Call the handler method with the data
                    handler_method(data)
                execute_in_main_thread(execute_handler, ())
            else:
                logging.warning(f"No handler found for command: {command}")

        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON message: {e}")
        except Exception as e:
            logging.error(f"Error processing WebSocket message: {e}")
            import traceback
            traceback.print_exc()

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
        subcommands = params.get('subcommands', {})
        preview_renderer = self.controllers.create_preview_renderer()

        try:
            # Process subcommands for updates before rendering
            if 'camera' in subcommands:
                camera_data = subcommands['camera']
                result = self.controllers.set_active_camera(
                    camera_data.get('camera_name'))
                logging.info(f"Camera update result: {result}")

            if 'lights' in subcommands:
                light_update = subcommands['lights']
                result = self.controllers.update_light(
                    light_update.get('light_name'),
                    color=light_update.get('color'),
                    strength=light_update.get('strength')
                )
                logging.info(f"Light update result: {result}")

            if 'materials' in subcommands:
                for material_update in subcommands['materials']:
                    result = self.controllers.update_material(
                        material_update.get('material_name'),
                        color=material_update.get('color'),
                        roughness=material_update.get('roughness'),
                        metallic=material_update.get('metallic')
                    )
                    logging.info(f"Material update result: {result}")

            if 'objects' in subcommands:
                for object_update in subcommands['objects']:
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

            # Render multiple frames (e.g., 24 frames)
            num_frames = params.get('num_frames', 24)
            for frame in range(1, num_frames + 1):
                preview_renderer.render_preview_frame(frame)

            self._send_response('start_broadcast', True)

        except Exception as e:
            logging.error(f"Preview rendering error: {e}")
            import traceback
            traceback.print_exc()
            self._send_response('Preview Rendering failed', False)

    def _handle_rescan_template(self):
        """Rescan the controllable objects and send the response"""
        try:
            controllables = self.wizard.scan_controllable_objects()
            # Send the template controls with the actual controllables data
            self._send_response('template_controls', True, controllables)
        except Exception as e:
            logging.error(f"Error during template rescan: {e}")
            self._send_response('template_scan_result', False)

    def _send_response(self, command, result, data=None):
        """
        Send a WebSocket response.

        :param command: The command to send (e.g., 'template_controls')
        :param result: Boolean indicating success or failure
        :param data: Optional additional data to send (e.g., controllables object)
        """
        status = 'success' if result else 'failed'

        response = {
            'command': command,
            'status': status
        }

        # Include the data in the response if provided
        if data is not None:
            response['data'] = data

        # Convert the response dictionary to a JSON string
        json_response = json.dumps(response)

        # Send the response via WebSocket
        self.ws.send(json_response)

    def _on_close(self, ws, close_status_code, close_msg):
        logging.info(
            f"WebSocket connection closed. Status: {close_status_code}, Message: {close_msg}")

    def _on_error(self, ws, error):
        logging.error(f"WebSocket error: {error}")


# Singleton instance for easy access
websocket_handler = WebSocketHandler()


def register():
    """Register WebSocket handler"""
    websocket_handler.connect()


def unregister():
    """Unregister WebSocket handler"""
    websocket_handler.disconnect()
