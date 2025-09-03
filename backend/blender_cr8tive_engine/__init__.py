"""
Blender AI Router - Main AI orchestration addon for Blender
Discovers and routes commands to AI-capable addons
"""

import bpy
import logging
from pathlib import Path
from .registry import AIAddonRegistry, AICommandRouter
from . import ws

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bl_info = {
    "name": "Blender AI Router",
    "author": "Cr8-xyz <thamsanqa.dev@gmail.com>",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Tools",
    "description": "Main AI router for discovering and routing commands to AI-capable addons",
    "warning": "",
    "wiki_url": "https://code.streetcrisis.online/Cr8-xyz/cr8-app",
    "category": "Development",
}

# Global instances
_registry = None
_router = None


def get_registry():
    """Get the global addon registry instance"""
    global _registry
    if _registry is None:
        _registry = AIAddonRegistry()
    return _registry


def get_router():
    """Get the global command router instance"""
    global _router
    if _router is None:
        _router = AICommandRouter(get_registry())
    return _router


# Router's own command handlers (for system commands)
def handle_get_available_addons() -> dict:
    """Get list of all registered AI-capable addons"""
    try:
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
        registry = get_registry()
        new_count = registry.refresh_registry()

        # Send registry update event
        from .ws.websocket_handler import get_handler
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


# Navigation command handlers
def handle_frame_jump_start() -> dict:
    """Jump to animation start frame"""
    try:
        bpy.ops.screen.frame_jump(end=False)
        current_frame = bpy.context.scene.frame_current
        return {
            "status": "success",
            "message": f"Jumped to start frame ({current_frame})",
            "data": {"current_frame": current_frame}
        }
    except Exception as e:
        logger.error(f"Error jumping to start frame: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to jump to start frame: {str(e)}",
            "error_code": "FRAME_JUMP_ERROR"
        }


def handle_frame_jump_end() -> dict:
    """Jump to animation end frame"""
    try:
        bpy.ops.screen.frame_jump(end=True)
        current_frame = bpy.context.scene.frame_current
        return {
            "status": "success",
            "message": f"Jumped to end frame ({current_frame})",
            "data": {"current_frame": current_frame}
        }
    except Exception as e:
        logger.error(f"Error jumping to end frame: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to jump to end frame: {str(e)}",
            "error_code": "FRAME_JUMP_ERROR"
        }


def handle_keyframe_jump_prev() -> dict:
    """Jump to previous keyframe"""
    try:
        bpy.ops.screen.keyframe_jump(next=False)
        current_frame = bpy.context.scene.frame_current
        return {
            "status": "success",
            "message": f"Jumped to previous keyframe ({current_frame})",
            "data": {"current_frame": current_frame}
        }
    except Exception as e:
        logger.error(f"Error jumping to previous keyframe: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to jump to previous keyframe: {str(e)}",
            "error_code": "KEYFRAME_JUMP_ERROR"
        }


def handle_keyframe_jump_next() -> dict:
    """Jump to next keyframe"""
    try:
        bpy.ops.screen.keyframe_jump(next=True)
        current_frame = bpy.context.scene.frame_current
        return {
            "status": "success",
            "message": f"Jumped to next keyframe ({current_frame})",
            "data": {"current_frame": current_frame}
        }
    except Exception as e:
        logger.error(f"Error jumping to next keyframe: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to jump to next keyframe: {str(e)}",
            "error_code": "KEYFRAME_JUMP_ERROR"
        }


def handle_animation_play() -> dict:
    """Play animation forward"""
    try:
        bpy.ops.screen.animation_play()
        return {
            "status": "success",
            "message": "Animation playing forward",
            "data": {"animation_state": "playing"}
        }
    except Exception as e:
        logger.error(f"Error playing animation: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to play animation: {str(e)}",
            "error_code": "ANIMATION_PLAY_ERROR"
        }


def handle_animation_play_reverse() -> dict:
    """Play animation in reverse"""
    try:
        bpy.ops.screen.animation_play(reverse=True)
        return {
            "status": "success",
            "message": "Animation playing in reverse",
            "data": {"animation_state": "playing_reverse"}
        }
    except Exception as e:
        logger.error(f"Error playing animation in reverse: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to play animation in reverse: {str(e)}",
            "error_code": "ANIMATION_PLAY_ERROR"
        }


def handle_animation_pause() -> dict:
    """Pause animation"""
    try:
        bpy.ops.screen.animation_cancel(restore_frame=True)
        return {
            "status": "success",
            "message": "Animation paused",
            "data": {"animation_state": "paused"}
        }
    except Exception as e:
        logger.error(f"Error pausing animation: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to pause animation: {str(e)}",
            "error_code": "ANIMATION_PAUSE_ERROR"
        }


def handle_viewport_set_solid() -> dict:
    """Set viewport shading to solid"""
    try:
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces[0].shading.type = 'SOLID'
        return {
            "status": "success",
            "message": "Viewport set to solid shading",
            "data": {"viewport_mode": "solid"}
        }
    except Exception as e:
        logger.error(f"Error setting viewport to solid: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to set viewport to solid: {str(e)}",
            "error_code": "VIEWPORT_ERROR"
        }


def handle_viewport_set_rendered() -> dict:
    """Set viewport shading to rendered"""
    try:
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces[0].shading.type = 'RENDERED'
        return {
            "status": "success",
            "message": "Viewport set to rendered shading",
            "data": {"viewport_mode": "rendered"}
        }
    except Exception as e:
        logger.error(f"Error setting viewport to rendered: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to set viewport to rendered: {str(e)}",
            "error_code": "VIEWPORT_ERROR"
        }


# 3D Navigation helper functions
def ensure_view3d_context():
    """Ensure VIEW_3D context is available for viewport operations"""
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for region in area.regions:
                if region.type == 'WINDOW':
                    return {'area': area, 'region': region}
    return None


def pan_view_manual(direction, amount=0.5):
    """Manual pan by directly manipulating view_location using existing context"""
    context = ensure_view3d_context()
    if not context:
        raise Exception("No VIEW_3D area found")
    
    # Get the space from our already-found area
    area = context['area']
    space = area.spaces.active
    
    # Manipulate view_location directly
    if direction == 'PANLEFT': 
        space.region_3d.view_location.x -= amount
    elif direction == 'PANRIGHT': 
        space.region_3d.view_location.x += amount
    elif direction == 'PANUP': 
        space.region_3d.view_location.y += amount
    elif direction == 'PANDOWN': 
        space.region_3d.view_location.y -= amount


# 3D Navigation command handlers
def handle_orbit_left() -> dict:
    """Orbit view to the left"""
    try:
        context = ensure_view3d_context()
        if context:
            with bpy.context.temp_override(**context):
                bpy.ops.view3d.view_orbit(type='ORBITLEFT')
        else:
            return {
                "status": "error",
                "message": "No VIEW_3D region found",
                "error_code": "NAVIGATION_ERROR"
            }
        
        return {
            "status": "success",
            "message": "Orbited view left",
            "data": {"navigation_action": "orbit_left"}
        }
    except Exception as e:
        logger.error(f"Error orbiting left: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to orbit left: {str(e)}",
            "error_code": "NAVIGATION_ERROR"
        }


def handle_orbit_right() -> dict:
    """Orbit view to the right"""
    try:
        context = ensure_view3d_context()
        if context:
            with bpy.context.temp_override(**context):
                bpy.ops.view3d.view_orbit(type='ORBITRIGHT')
        else:
            return {
                "status": "error",
                "message": "No VIEW_3D region found",
                "error_code": "NAVIGATION_ERROR"
            }
        
        return {
            "status": "success",
            "message": "Orbited view right",
            "data": {"navigation_action": "orbit_right"}
        }
    except Exception as e:
        logger.error(f"Error orbiting right: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to orbit right: {str(e)}",
            "error_code": "NAVIGATION_ERROR"
        }


def handle_orbit_up() -> dict:
    """Orbit view up"""
    try:
        context = ensure_view3d_context()
        if context:
            with bpy.context.temp_override(**context):
                bpy.ops.view3d.view_orbit(type='ORBITUP')
        else:
            return {
                "status": "error",
                "message": "No VIEW_3D region found",
                "error_code": "NAVIGATION_ERROR"
            }
        
        return {
            "status": "success",
            "message": "Orbited view up",
            "data": {"navigation_action": "orbit_up"}
        }
    except Exception as e:
        logger.error(f"Error orbiting up: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to orbit up: {str(e)}",
            "error_code": "NAVIGATION_ERROR"
        }


def handle_orbit_down() -> dict:
    """Orbit view down"""
    try:
        context = ensure_view3d_context()
        if context:
            with bpy.context.temp_override(**context):
                bpy.ops.view3d.view_orbit(type='ORBITDOWN')
        else:
            return {
                "status": "error",
                "message": "No VIEW_3D region found",
                "error_code": "NAVIGATION_ERROR"
            }
        
        return {
            "status": "success",
            "message": "Orbited view down",
            "data": {"navigation_action": "orbit_down"}
        }
    except Exception as e:
        logger.error(f"Error orbiting down: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to orbit down: {str(e)}",
            "error_code": "NAVIGATION_ERROR"
        }


def handle_pan_left() -> dict:
    """Pan view to the left"""
    try:
        # Primary approach: Manual pan (reliable)
        pan_view_manual('PANLEFT')
        
        # Fallback approach: Operator (commented for testing in different Blender versions)
        # context = ensure_view3d_context()
        # if context:
        #     with bpy.context.temp_override(**context):
        #         bpy.ops.view3d.view_pan(type='PANLEFT')
        
        return {
            "status": "success",
            "message": "Panned view left",
            "data": {"navigation_action": "pan_left"}
        }
    except Exception as e:
        logger.error(f"Error panning left: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to pan left: {str(e)}",
            "error_code": "NAVIGATION_ERROR"
        }


def handle_pan_right() -> dict:
    """Pan view to the right"""
    try:
        # Primary approach: Manual pan (reliable)
        pan_view_manual('PANRIGHT')
        
        # Fallback approach: Operator (commented for testing in different Blender versions)
        # context = ensure_view3d_context()
        # if context:
        #     with bpy.context.temp_override(**context):
        #         bpy.ops.view3d.view_pan(type='PANRIGHT')
        
        return {
            "status": "success",
            "message": "Panned view right",
            "data": {"navigation_action": "pan_right"}
        }
    except Exception as e:
        logger.error(f"Error panning right: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to pan right: {str(e)}",
            "error_code": "NAVIGATION_ERROR"
        }


def handle_pan_up() -> dict:
    """Pan view up"""
    try:
        # Primary approach: Manual pan (reliable)
        pan_view_manual('PANUP')
        
        # Fallback approach: Operator (commented for testing in different Blender versions)
        # context = ensure_view3d_context()
        # if context:
        #     with bpy.context.temp_override(**context):
        #         bpy.ops.view3d.view_pan(type='PANUP')
        
        return {
            "status": "success",
            "message": "Panned view up",
            "data": {"navigation_action": "pan_up"}
        }
    except Exception as e:
        logger.error(f"Error panning up: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to pan up: {str(e)}",
            "error_code": "NAVIGATION_ERROR"
        }


def handle_pan_down() -> dict:
    """Pan view down"""
    try:
        # Primary approach: Manual pan (reliable)
        pan_view_manual('PANDOWN')
        
        # Fallback approach: Operator (commented for testing in different Blender versions)
        # context = ensure_view3d_context()
        # if context:
        #     with bpy.context.temp_override(**context):
        #         bpy.ops.view3d.view_pan(type='PANDOWN')
        
        return {
            "status": "success",
            "message": "Panned view down",
            "data": {"navigation_action": "pan_down"}
        }
    except Exception as e:
        logger.error(f"Error panning down: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to pan down: {str(e)}",
            "error_code": "NAVIGATION_ERROR"
        }


def handle_zoom_in() -> dict:
    """Zoom in to the viewport"""
    try:
        context = ensure_view3d_context()
        if context:
            with bpy.context.temp_override(**context):
                bpy.ops.view3d.zoom(delta=1)
        else:
            return {
                "status": "error",
                "message": "No VIEW_3D region found",
                "error_code": "NAVIGATION_ERROR"
            }
        
        return {
            "status": "success",
            "message": "Zoomed in",
            "data": {"navigation_action": "zoom_in"}
        }
    except Exception as e:
        logger.error(f"Error zooming in: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to zoom in: {str(e)}",
            "error_code": "NAVIGATION_ERROR"
        }


def handle_zoom_out() -> dict:
    """Zoom out from the viewport"""
    try:
        context = ensure_view3d_context()
        if context:
            with bpy.context.temp_override(**context):
                bpy.ops.view3d.zoom(delta=-1)
        else:
            return {
                "status": "error",
                "message": "No VIEW_3D region found",
                "error_code": "NAVIGATION_ERROR"
            }
        
        return {
            "status": "success",
            "message": "Zoomed out",
            "data": {"navigation_action": "zoom_out"}
        }
    except Exception as e:
        logger.error(f"Error zooming out: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to zoom out: {str(e)}",
            "error_code": "NAVIGATION_ERROR"
        }


def handle_get_viewport_screenshot(max_size=800, filepath=None, format="png") -> dict:
    """
    Capture a screenshot of the current 3D viewport, save it, and return image data for analysis.
    
    Parameters:
    - max_size: Maximum size in pixels for the largest dimension of the image
    - filepath: Path where to save the screenshot file
    - format: Image format (png, jpg, etc.)
    
    Returns success/error status with image data
    """
    import base64
    
    try:
        if not filepath:
            return {
                "status": "error",
                "message": "No filepath provided",
                "error_code": "INVALID_PARAMETERS"
            }
        
        # Find the active 3D viewport
        area = None
        for a in bpy.context.screen.areas:
            if a.type == 'VIEW_3D':
                area = a
                break
        
        if not area:
            return {
                "status": "error",
                "message": "No 3D viewport found",
                "error_code": "VIEWPORT_NOT_FOUND"
            }
        
        # Take screenshot with proper context override
        with bpy.context.temp_override(area=area):
            bpy.ops.screen.screenshot_area(filepath=filepath)
        
        # Load and resize if needed
        img = bpy.data.images.load(filepath)
        width, height = img.size
        
        if max(width, height) > max_size:
            scale = max_size / max(width, height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            img.scale(new_width, new_height)
            
            # Set format and save
            img.file_format = format.upper()
            img.save()
            width, height = new_width, new_height
        
        # Cleanup Blender image data
        bpy.data.images.remove(img)
        
        # Verify file exists and read image data
        from pathlib import Path
        file_path = Path(filepath)
        if not file_path.exists():
            return {
                "status": "error",
                "message": "Screenshot file was not created successfully",
                "error_code": "FILE_NOT_CREATED"
            }
        
        # Read image file and convert to base64 for transmission
        try:
            with open(filepath, 'rb') as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Error reading screenshot file: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to read screenshot file: {str(e)}",
                "error_code": "FILE_READ_ERROR"
            }
        
        return {
            "status": "success",
            "message": f"Screenshot captured and loaded: {width}x{height}",
            "data": {
                "width": width,
                "height": height,
                "filepath": filepath,
                "format": format,
                "image_data": image_data,
                "media_type": f"image/{format.lower()}"
            }
        }
        
    except Exception as e:
        logger.error(f"Error capturing viewport screenshot: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to capture screenshot: {str(e)}",
            "error_code": "SCREENSHOT_ERROR"
        }


# Export command handlers for the router addon itself
AI_COMMAND_HANDLERS = {
    'get_available_addons': handle_get_available_addons,
    'get_addon_info': handle_get_addon_info,
    'refresh_addons': handle_refresh_addons,
    # Animation controls
    'frame_jump_start': handle_frame_jump_start,
    'frame_jump_end': handle_frame_jump_end,
    'keyframe_jump_prev': handle_keyframe_jump_prev,
    'keyframe_jump_next': handle_keyframe_jump_next,
    'animation_play': handle_animation_play,
    'animation_play_reverse': handle_animation_play_reverse,
    'animation_pause': handle_animation_pause,
    # Viewport controls
    'viewport_set_solid': handle_viewport_set_solid,
    'viewport_set_rendered': handle_viewport_set_rendered,
    'get_viewport_screenshot': handle_get_viewport_screenshot,
    # 3D Navigation controls
    'orbit_left': handle_orbit_left,
    'orbit_right': handle_orbit_right,
    'orbit_up': handle_orbit_up,
    'orbit_down': handle_orbit_down,
    'pan_left': handle_pan_left,
    'pan_right': handle_pan_right,
    'pan_up': handle_pan_up,
    'pan_down': handle_pan_down,
    'zoom_in': handle_zoom_in,
    'zoom_out': handle_zoom_out,
}


def register():
    """Register the AI router addon"""
    try:
        logger.info("Registering Blender AI Router...")

        # Register WebSocket system
        ws.register()

        # Initialize registry and router
        registry = get_registry()
        router = get_router()

        logger.info(
            f"AI Router registered with {len(registry.get_registered_addons())} addons")

    except Exception as e:
        logger.error(f"Failed to register AI Router: {str(e)}")
        raise


def unregister():
    """Unregister the AI router addon"""
    try:
        logger.info("Unregistering Blender AI Router...")

        # Unregister WebSocket system
        ws.unregister()

        # Clear global instances
        global _registry, _router
        _registry = None
        _router = None

        logger.info("AI Router unregistered")

    except Exception as e:
        logger.error(f"Failed to unregister AI Router: {str(e)}")


if __name__ == "__main__":
    register()
