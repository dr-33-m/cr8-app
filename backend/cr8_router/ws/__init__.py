"""
WebSocket module for blender_cr8tive_engine.
This module provides a modular approach to handling WebSocket communication.
"""

from .websocket_handler import WebSocketHandler, get_handler, register, unregister
from .handlers import (
    register_event_handlers,
    process_message,
    handle_addon_command,
    route_command_to_addon,
    send_registry_update,
    handle_ping,
    handle_connection_confirmation,
    execute_in_main_thread,
    ConnectWebSocketOperator,
    register_blender,
    unregister_blender,
)

__all__ = [
    'WebSocketHandler',
    'get_handler',
    'register',
    'unregister',
    'register_event_handlers',
    'process_message',
    'handle_addon_command',
    'route_command_to_addon',
    'send_registry_update',
    'handle_ping',
    'handle_connection_confirmation',
    'execute_in_main_thread',
    'ConnectWebSocketOperator',
    'register_blender',
    'unregister_blender',
]
