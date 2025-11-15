"""
Registry command handlers for the Blender AI Router
Handles system commands for addon management and registry operations
"""

import logging
from ..registry import AIAddonRegistry

logger = logging.getLogger(__name__)


def handle_get_available_addons() -> dict:
    """Get list of all registered AI-capable addons"""
    try:
        from .. import get_registry
        registry = get_registry()
        addons = registry.get_registered_addons()

        addon_list = []
        for addon_id, manifest in addons.items():
            addon_info = {
                'id': addon_id,
                'name': manifest.addon_info.get('name', addon_id),
                'version': manifest.addon_info.get('version', 'unknown'),
                'author': manifest.addon_info.get('author', 'unknown'),
                'category': manifest.addon_info.get('category', 'unknown'),
                'description': manifest.addon_info.get('description', ''),
                'tool_count': len(manifest.get_tools())
            }
            addon_list.append(addon_info)

        return {
            "status": "success",
            "message": f"Found {len(addon_list)} registered AI addons",
            "data": {
                "addons": addon_list,
                "total_count": len(addon_list)
            }
        }
    except Exception as e:
        logger.error(f"Error getting available addons: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to get available addons: {str(e)}",
            "error_code": "REGISTRY_ERROR"
        }


def handle_get_addon_info(addon_id: str) -> dict:
    """Get detailed information about a specific addon"""
    try:
        from .. import get_registry
        registry = get_registry()
        manifest = registry.get_addon_manifest(addon_id)

        if not manifest:
            return {
                "status": "error",
                "message": f"Addon '{addon_id}' not found",
                "error_code": "ADDON_NOT_FOUND"
            }

        # Get detailed addon information
        addon_info = {
            'basic_info': manifest.addon_info,
            'ai_integration': {
                'agent_description': manifest.ai_integration.get('agent_description', ''),
                'context_hints': manifest.ai_integration.get('context_hints', []),
                'requirements': manifest.ai_integration.get('requirements', {}),
                'metadata': manifest.ai_integration.get('metadata', {})
            },
            'tools': manifest.get_tools(),
            'handlers_loaded': addon_id in registry.addon_handlers,
            'is_valid': manifest.is_valid
        }

        return {
            "status": "success",
            "message": f"Retrieved information for addon '{addon_id}'",
            "data": {
                "addon_info": addon_info
            }
        }
    except Exception as e:
        logger.error(f"Error getting addon info for {addon_id}: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to get addon info: {str(e)}",
            "error_code": "INFO_RETRIEVAL_ERROR"
        }


def handle_refresh_addons() -> dict:
    """Refresh the addon registry by scanning for new addons"""
    try:
        from .. import get_registry
        registry = get_registry()
        new_count = registry.refresh_registry()

        # Send registry update event
        from ..ws.websocket_handler import get_handler
        handler = get_handler()
        if handler and handler.ws:
            import json
            registry_event = {
                "type": "registry_updated",
                "total_addons": new_count,
                "available_tools": registry.get_available_tools()
            }
            handler.ws.send(json.dumps(registry_event))

        return {
            "status": "success",
            "message": f"Registry refreshed. Found {new_count} AI addons",
            "data": {
                "addon_count": new_count
            }
        }
    except Exception as e:
        logger.error(f"Error refreshing addon registry: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to refresh registry: {str(e)}",
            "error_code": "REFRESH_ERROR"
        }
