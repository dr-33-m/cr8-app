"""
Blender-specific handlers for WebSocket communication.
Handles Blender integration, main thread execution, and operator registration.
"""

import logging
import bpy

logger = logging.getLogger(__name__)


def execute_in_main_thread(function, args):
    """
    Execute a function in Blender's main thread.
    
    Args:
        function: Function to execute
        args: Arguments to pass to the function
    """
    def wrapper():
        function(*args)
        return None
    bpy.app.timers.register(wrapper, first_interval=0.0)


class ConnectWebSocketOperator(bpy.types.Operator):
    """Blender operator for connecting to WebSocket server."""
    bl_idname = "ws_handler.connect_websocket"
    bl_label = "Connect Socket.IO"
    bl_description = "Initialize Socket.IO connection to Cr8tive Engine server"

    def execute(self, context):
        try:
            from ..websocket_handler import get_handler
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


def register_blender():
    """Register Blender operator and handlers."""
    try:
        bpy.utils.register_class(ConnectWebSocketOperator)
        logger.info("Registered WebSocket operator")
    except Exception as e:
        logger.error(f"Error registering Blender operator: {e}")


def unregister_blender():
    """Unregister Blender operator and handlers."""
    try:
        bpy.utils.unregister_class(ConnectWebSocketOperator)
        logger.info("Unregistered WebSocket operator")
    except Exception as e:
        logger.error(f"Error unregistering Blender operator: {e}")
