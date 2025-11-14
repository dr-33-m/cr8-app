"""
Viewport Control Handlers
Handles all viewport-related commands for the Blender Controls addon
"""

import bpy
import logging
import base64
from pathlib import Path

logger = logging.getLogger(__name__)


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


def handle_get_viewport_screenshot(max_size=800, filepath=None, format="png") -> dict:
    """
    Capture a screenshot of the current 3D viewport, save it, and return image data for analysis.

    Parameters:
    - max_size: Maximum size in pixels for the largest dimension of the image
    - filepath: Path where to save the screenshot file
    - format: Image format (png, jpg, etc.)

    Returns success/error status with image data
    """
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
