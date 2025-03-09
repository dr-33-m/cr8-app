"""
WebSocket module for blender_cr8tive_engine.
This module provides a modular approach to handling WebSocket communication.
"""

from .websocket_handler import WebSocketHandler, get_handler, register, unregister

__all__ = ['WebSocketHandler', 'get_handler', 'register', 'unregister']
