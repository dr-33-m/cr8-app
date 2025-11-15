"""
WebSocket handlers module for cr8_router.
Provides separated concerns for event handling, command processing, and utilities.
"""

from .event_handlers import register_event_handlers
from .command_handlers import process_message, handle_addon_command, route_command_to_addon
from .registry_handlers import send_registry_update
from .utility_handlers import handle_ping, handle_connection_confirmation
from .blender_handlers import execute_in_main_thread, ConnectWebSocketOperator, register_blender, unregister_blender

__all__ = [
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
