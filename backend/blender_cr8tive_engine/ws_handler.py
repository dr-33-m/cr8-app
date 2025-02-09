import os
import bpy
import re
import json
import uuid
import threading
import logging
import websocket
from .template_wizard import TemplateWizard
from .blender_controllers import BlenderControllers
from .video_generator import GenerateVideo
import tempfile
from pathlib import Path
import ssl
import time
import numpy as np
from typing import Optional

# WebRTC related imports
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer, RTCIceCandidate
from aiortc.contrib.media import MediaStreamTrack, MediaBlackhole
from av import VideoFrame

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class BlenderVideoStreamTrack(MediaStreamTrack):
    """A video stream track that captures frames from Blender's viewport."""
    kind = "video"

    def __init__(self, preview_renderer):
        super().__init__()
        self._preview_renderer = preview_renderer
        self._frame_count = 0
        self._start_time = time.time()
        self._frame_buffer = []
        self._lock = threading.Lock()

    def add_frame(self, frame_data):
        """Add a new frame to the buffer."""
        with self._lock:
            # Convert frame data to numpy array
            frame = np.frombuffer(
                frame_data, dtype=np.uint8).reshape(720, 1280, 4)
            # Remove alpha channel
            frame = frame[:, :, :3]
            self._frame_buffer.append(frame)

    async def recv(self):
        """Get the next frame."""
        pts = int((time.time() - self._start_time) * 1000)  # milliseconds
        self._frame_count += 1

        frame = None
        with self._lock:
            if self._frame_buffer:
                frame_data = self._frame_buffer.pop(0)
                frame = VideoFrame.from_ndarray(frame_data, format="rgb24")
            else:
                # Create black frame if no data available
                frame = VideoFrame.from_ndarray(
                    np.zeros((720, 1280, 3), dtype=np.uint8),
                    format="rgb24"
                )

        frame.pts = pts
        frame.time_base = 1/1000  # milliseconds
        return frame


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
        'webrtc': '_handle_webrtc_signaling'
    }

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(WebSocketHandler, cls).__new__(cls)
            cls._instance._initialized = False
            cls._instance.lock = threading.Lock()
            cls._instance.ws = None
            cls._instance.url = None
            cls._instance.username = None
            cls._instance.peer_connection = None
            cls._instance.video_track = None
            cls._instance._initialized = True
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = False
            self.lock = threading.Lock()
            self.ws = None
            self.url = None
            self.username = None
            self.peer_connection = None
            self.video_track = None
            self.data_channel = None
            self.wizard = TemplateWizard()
            self.controllers = BlenderControllers()
            self._initialized = True

    def initialize_connection(self, url=None):
        """Call this explicitly when ready to connect"""
        if self.ws:
            return  # Already connected

        self.url = url or os.environ.get("WS_URL")

        match = re.match(
            r'ws[s]?://([^:/]+)(?::\d+)?/ws/([^/]+)/blender', self.url)
        if match:
            self.host = match.group(1)
            self.username = match.group(2)
        else:
            raise ValueError(
                "Invalid WebSocket URL format. Unable to extract username."
            )

        if not self.url:
            raise ValueError(
                "WebSocket URL must be set via WS_URL environment variable "
                "or passed to initialize_connection()"
            )

        self.ws = None
        self.wizard = TemplateWizard()
        self.controllers = BlenderControllers()
        self.processing_complete = threading.Event()
        self.processed_commands = set()
        self.reconnect_attempts = 0
        self.max_retries = 5
        self.stop_retries = False

        # Initialize WebRTC configuration
        self.rtc_config = RTCConfiguration([
            RTCIceServer(urls="stun:stun.l.google.com:19302")
        ])

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
        """Disconnect WebSocket and cleanup resources"""
        with self.lock:
            self.processing_complete.set()
            self.stop_retries = True

            # Close WebSocket connection
            if self.ws and self.ws.sock and self.ws.sock.connected:
                self.ws.close()
                self.ws = None

            # Close WebRTC connection
            if self.peer_connection:
                self.peer_connection.close()
                self.peer_connection = None

            # Close data channel
            if self.data_channel:
                self.data_channel.close()
                self.data_channel = None

            # Stop video track
            if self.video_track:
                self.video_track.stop()
                self.video_track = None

            # Join WebSocket thread
            if self.ws_thread:
                self.ws_thread.join(timeout=2)
                self.ws_thread = None

    def _on_open(self, ws):
        """Handle WebSocket open event"""
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
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            command = data.get('command')

            if command in self.command_handlers:
                handler_name = self.command_handlers[command]
                handler = getattr(self, handler_name)
                execute_in_main_thread(handler, (data,))
            else:
                logging.warning(f"Unhandled command: {command}")

        except json.JSONDecodeError:
            logging.error("Failed to decode message as JSON")
        except Exception as e:
            logging.error(f"Error processing message: {str(e)}")

    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close event"""
        logging.info(
            f"WebSocket connection closed. Status: {close_status_code}, Message: {close_msg}")
        self.processing_complete.set()

    def _on_error(self, ws, error):
        """Handle WebSocket error event"""
        logging.error(f"WebSocket error: {error}")
        self.reconnect_attempts += 1
        if self.reconnect_attempts >= self.max_retries:
            logging.error("Max retries reached. Stopping WebSocket attempts.")
            self.stop_retries = True
            self.processing_complete.set()

    async def _handle_webrtc_signaling(self, data):
        """Handle WebRTC signaling messages"""
        try:
            signal_type = data.get("signalType")
            signal_data = data.get("signalData")

            if signal_type == "offer":
                # Create new RTCPeerConnection
                self.peer_connection = RTCPeerConnection(
                    configuration=self.rtc_config)

                # Create and add video track
                if not self.video_track:
                    self.video_track = BlenderVideoStreamTrack(
                        self.controllers.preview_renderer)
                self.peer_connection.addTrack(self.video_track)

                # Create data channel for controls
                self.data_channel = self.peer_connection.createDataChannel(
                    "controls")
                self.data_channel.onmessage = self._handle_data_channel_message
                self.data_channel.onopen = self._handle_data_channel_open

                # Set the remote description
                offer = RTCSessionDescription(
                    sdp=signal_data["sdp"],
                    type=signal_data["type"]
                )
                await self.peer_connection.setRemoteDescription(offer)

                # Create and send answer
                answer = await self.peer_connection.createAnswer()
                await self.peer_connection.setLocalDescription(answer)

                # Send answer back through WebSocket
                self._send_response("webrtc", True, {
                    "signalType": "answer",
                    "signalData": {
                        "sdp": self.peer_connection.localDescription.sdp,
                        "type": self.peer_connection.localDescription.type
                    }
                })

            elif signal_type == "ice-candidate":
                if self.peer_connection:
                    candidate = RTCIceCandidate(
                        sdpMid=signal_data["sdpMid"],
                        sdpMLineIndex=signal_data["sdpMLineIndex"],
                        candidate=signal_data["candidate"]
                    )
                    await self.peer_connection.addIceCandidate(candidate)

        except Exception as e:
            logging.error(f"WebRTC signaling error: {str(e)}")
            self._send_response("webrtc", False, {
                "error": str(e)
            })

    def _handle_preview_rendering(self, data):
        """Handle preview rendering with WebRTC streaming"""
        logging.info("Starting preview rendering with WebRTC")
        params = data.get('params', {})
        preview_renderer = self.controllers.create_preview_renderer(
            self.username, webrtc_track=self.video_track)

        try:
            # Process scene updates
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

            # Start WebRTC streaming
            preview_renderer.setup_preview_render(params)
            bpy.ops.render.opengl(animation=True)

            self._send_response('start_broadcast', True)

        except Exception as e:
            logging.error(f"Preview rendering error: {e}")
            import traceback
            traceback.print_exc()
            self._send_response('Preview Rendering failed', False)

    def _handle_data_channel_message(self, event):
        """Handle incoming data channel messages"""
        try:
            data = json.loads(event.data)
            command = data.get('command')

            if command == 'rescan_template':
                self._handle_rescan_template(data)
            elif command == 'generate_video':
                self._handle_generate_video(data)
            elif command == 'change_camera':
                self._handle_camera_change(data)
            elif command == 'update_light':
                self._handle_light_update(data)
            elif command == 'update_material':
                self._handle_material_update(data)
            elif command == 'update_object':
                self._handle_object_transformation(data)

        except Exception as e:
            logging.error(f"Error handling data channel message: {e}")
            self._send_error_message(str(e))

    def _handle_data_channel_open(self, event):
        """Handle data channel open event"""
        logging.info("Data channel opened")
        # Send initial template controls
        self._handle_rescan_template({"message_id": str(uuid.uuid4())})

    def _send_control_message(self, message_type: str, data: dict):
        """Send control message through data channel or WebSocket"""
        try:
            message = {
                "type": message_type,
                "data": data,
                "timestamp": time.time()
            }

            if self.data_channel and self.data_channel.readyState == "open":
                self.data_channel.send(json.dumps(message))
            elif self.ws:
                self.ws.send(json.dumps(message))

        except Exception as e:
            logging.error(f"Error sending control message: {e}")

    def _handle_rescan_template(self, data):
        """Handle template rescan request"""
        try:
            message_id = data.get('message_id')
            logging.info(
                f"Handling template rescan request with message_id: {message_id}")

            controllables = self.wizard.scan_controllable_objects()
            logging.info(f"Scanned {len(controllables)} controllable objects")

            result = {
                "command": "template_controls",
                "data": {
                    "controllables": controllables,
                    "message_id": message_id
                },
                "status": "success"
            }

            self._send_control_message("template_controls", result)

        except Exception as e:
            logging.error(f"Error during template rescan: {e}")
            self._send_error_message(str(e))

    def _handle_generate_video(self, data):
        """Handle video generation request"""
        try:
            message_id = data.get('message_id')
            image_sequence_directory = Path(
                f"/mnt/shared_storage/Cr8tive_Engine/Sessions/{self.username}") / "preview"
            output_file = image_sequence_directory / "preview.mp4"
            resolution = (1280, 720)
            fps = 30

            image_sequence_directory.mkdir(parents=True, exist_ok=True)
            image_files = list(image_sequence_directory.glob('*.png'))

            if not image_files:
                raise ValueError(
                    "No image files found in the specified directory")

            video_generator = GenerateVideo(
                str(image_sequence_directory),
                str(output_file),
                resolution,
                fps
            )
            video_generator.gen_video_from_images()

            result = {
                "command": "generate_video",
                "status": "completed",
                "message_id": message_id
            }

            self._send_control_message("video_generation", result)

        except Exception as e:
            logging.error(f"Video generation error: {e}")
            self._send_error_message(str(e))

    def _send_error_message(self, error_msg: str):
        """Send error message through available channel"""
        message = {
            "status": "error",
            "message": error_msg,
            "timestamp": time.time()
        }

        if self.data_channel and self.data_channel.readyState == "open":
            self.data_channel.send(json.dumps(message))
        elif self.ws:
            self.ws.send(json.dumps(message))

    def _handle_camera_change(self, data):
        """Handle camera change request"""
        try:
            result = self.controllers.set_active_camera(
                data.get('camera_name'))
            self._send_control_message("camera_change", {
                "success": result,
                "message_id": data.get('message_id')
            })
        except Exception as e:
            logging.error(f"Error changing camera: {e}")
            self._send_error_message(str(e))

    def _handle_light_update(self, data):
        """Handle light update request"""
        try:
            result = self.controllers.update_light(
                data.get('light_name'),
                color=data.get('color'),
                strength=data.get('strength')
            )
            self._send_control_message("light_update", {
                "success": result,
                "message_id": data.get('message_id')
            })
        except Exception as e:
            logging.error(f"Error updating light: {e}")
            self._send_error_message(str(e))

    def _handle_material_update(self, data):
        """Handle material update request"""
        try:
            result = self.controllers.update_material(
                data.get('material_name'),
                color=data.get('color'),
                roughness=data.get('roughness'),
                metallic=data.get('metallic')
            )
            self._send_control_message("material_update", {
                "success": result,
                "message_id": data.get('message_id')
            })
        except Exception as e:
            logging.error(f"Error updating material: {e}")
            self._send_error_message(str(e))

    def _handle_object_transformation(self, data):
        """Handle object transformation request"""
        try:
            result = self.controllers.update_object(
                data.get('object_name'),
                location=data.get('location'),
                rotation=data.get('rotation'),
                scale=data.get('scale')
            )
            self._send_control_message("object_update", {
                "success": result,
                "message_id": data.get('message_id')
            })
        except Exception as e:
            logging.error(f"Error updating object: {e}")
            self._send_error_message(str(e))

    def _send_response(self, command: str, success: bool, data: dict = None):
        """Send response through available channel"""
        message = {
            "command": command,
            "status": "success" if success else "failed",
            "data": data,
            "timestamp": time.time()
        }

        if self.data_channel and self.data_channel.readyState == "open":
            self.data_channel.send(json.dumps(message))
        elif self.ws:
            self.ws.send(json.dumps(message))


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
    handler = WebSocketHandler()
    handler.disconnect()
