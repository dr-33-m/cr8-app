"""
Socket.IO event handlers for WebSocket communication.
Handles connection, disconnection, and message reception events.
"""

import logging
from ..message_types import MessageType
from .blender_handlers import execute_in_main_thread
from .command_handlers import process_message
from .registry_handlers import send_registry_update

logger = logging.getLogger(__name__)


def register_event_handlers(handler):
    """
    Register all Socket.IO event handlers on the handler instance.
    
    Args:
        handler: WebSocketHandler instance with sio client
    """
    
    @handler.sio.on('connect', namespace='/blender')
    def on_connect():
        logger.info("Connected to Socket.IO server")
        handler.processing_complete.clear()

        def send_init_message():
            try:
                # Send connection status via Socket.IO emit
                handler.sio.emit(
                    'connection_status',
                    {
                        'status': 'Connected',
                        'message': 'Blender registered'
                    },
                    namespace='/blender'
                )
                logger.info("Sent connection status to server")

                # Send registry update
                send_registry_update(handler.sio)
                
                # Start WebRTC streaming
                start_streaming()
            except Exception as e:
                logger.error(f"Error in on_connect: {e}")

        def start_streaming():
            """Start WebRTC viewport streaming with dynamic producer ID"""
            try:
                import bpy
                import os
                
                username = os.environ.get("CR8_USERNAME")
                signaller_uri = os.environ.get("CR8_SIGNALLER_URI", "ws://127.0.0.1:8443")
                
                if not username:
                    logger.error("CR8_USERNAME not set, cannot start streaming")
                    return
                
                producer_id = f"blender-{username}"
                
                logger.info(f"Starting WebRTC streaming with producer_id: {producer_id}")
                
                # Configure streaming
                bpy.app.streaming.configure(
                    producer_id=producer_id,
                    signaller_uri=signaller_uri,
                    width=1920,
                    height=1080,
                    fps=30
                )
                
                # Start streaming
                bpy.app.streaming.start()
                
                logger.info(f"WebRTC streaming started successfully for {username}")
            except Exception as e:
                logger.error(f"Failed to start WebRTC streaming: {e}")

        execute_in_main_thread(send_init_message, ())

    @handler.sio.on('disconnect', namespace='/blender')
    def on_disconnect(reason):
        import bpy
        logger.info(f"Disconnected from server: {reason}")
        handler.processing_complete.set()
        handler.processing_commands.clear()
        
        # Stop WebRTC streaming
        try:
            if bpy.app.streaming.is_active():
                bpy.app.streaming.stop()
                logger.info("WebRTC streaming stopped on disconnect")
        except Exception as e:
            logger.error(f"Failed to stop WebRTC streaming: {e}")
        
        # Start 5-minute cleanup timer when server disconnects
        # We use a Blender timer to check reconnection status instead of time.sleep()
        # to avoid KeyboardInterrupt interrupting the sleep
        def check_and_start_cleanup():
            try:
                logger.info("Checking if Socket.IO reconnection has been exhausted...")
                
                # Check if still disconnected (reconnection exhausted)
                if not handler.sio.connected:
                    logger.warning("Server unreachable after reconnection attempts exhausted")
                    handler.start_server_cleanup_timer()
                    logger.info("Server cleanup timer started successfully")
                else:
                    logger.info("Socket.IO reconnected successfully, cleanup timer not needed")
            except Exception as e:
                logger.error(f"Failed to check reconnection status: {e}", exc_info=True)
            
            return None  # Unregister the timer after execution
        
        # Register a Blender timer to check reconnection status after ~40 seconds
        # This gives Socket.IO time to exhaust all 5 reconnection attempts
        # (delays: 2.25s, 3.83s, 8.16s, 9.95s, 10.41s = ~34 seconds total)
        try:
            bpy.app.timers.register(
                check_and_start_cleanup,
                first_interval=40.0
            )
            logger.info("Registered reconnection check timer for 40 seconds")
        except Exception as e:
            logger.error(f"Failed to register reconnection check timer: {e}", exc_info=True)
            # Fallback: try to start cleanup immediately if timer registration fails
            try:
                handler.start_server_cleanup_timer()
            except Exception as fallback_error:
                logger.error(f"Fallback cleanup timer also failed: {fallback_error}", exc_info=True)

    @handler.sio.on('connect_error', namespace='/blender')
    def on_connect_error(data):
        logger.error(f"Connection error: {data}")

    @handler.sio.on(MessageType.COMMAND_RECEIVED, namespace='/blender')
    def on_command_received(data):
        """Handle commands forwarded from backend (standardized)"""
        logger.info(f"Received {MessageType.COMMAND_RECEIVED}: {data}")

        def execute():
            process_message(data, handler)

        execute_in_main_thread(execute, ())

    @handler.sio.on('ping', namespace='/blender')
    def on_ping(data):
        """Handle ping events"""
        logger.info(f"Received ping: {data}")

        def execute():
            from .utility_handlers import handle_ping
            handle_ping(data, handler)

        execute_in_main_thread(execute, ())
