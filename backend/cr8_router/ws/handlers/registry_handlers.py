"""
Registry management handlers for WebSocket communication.
Handles sending registry updates to the server.
"""

import logging

logger = logging.getLogger(__name__)


def send_registry_update(sio):
    """
    Send registry update event to FastAPI via Socket.IO.
    
    Args:
        sio: Socket.IO client instance
    """
    try:
        from ... import get_registry
        registry = get_registry()

        available_tools = registry.get_available_tools()
        total_addons = len(registry.get_registered_addons())

        registry_event = {
            "type": "registry_updated",
            "total_addons": total_addons,
            "available_tools": available_tools
        }

        if sio and sio.connected:
            sio.emit('registry_update', registry_event, namespace='/blender')
            logger.info(
                f"Sent registry update to server: {total_addons} addons, {len(available_tools)} tools")
            logger.debug(f"Registry data: {registry_event}")

    except Exception as e:
        logger.error(f"Error sending registry update: {str(e)}")
        import traceback
        traceback.print_exc()
