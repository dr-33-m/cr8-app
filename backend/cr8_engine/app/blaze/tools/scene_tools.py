"""
Scene manipulation tools for B.L.A.Z.E Agent
Provides MCP tools for camera, light, material, and object controls.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class SceneTools:
    """Scene manipulation tools that wrap existing handlers"""

    def __init__(self, session_manager, handlers):
        """Initialize with session manager and handler references"""
        self.session_manager = session_manager
        self.camera_handler = handlers.get('camera')
        self.light_handler = handlers.get('light')
        self.material_handler = handlers.get('material')
        self.object_handler = handlers.get('object')
        self.logger = logging.getLogger(__name__)

    async def switch_camera(self, username: str, camera_name: str) -> str:
        """Switch to a specific camera in the scene"""
        try:
            if not self.camera_handler:
                return "Camera handler not available"

            await self.camera_handler.handle_update_camera(
                username=username,
                data={
                    "command": "update_camera",
                    "camera_name": camera_name
                },
                client_type="agent"
            )

            return f"Switched to camera: {camera_name}"

        except Exception as e:
            self.logger.error(f"Error switching camera: {str(e)}")
            return f"Error switching camera: {str(e)}"

    async def update_light_color(self, username: str, light_name: str, color: str) -> str:
        """Update the color of a specific light"""
        try:
            if not self.light_handler:
                return "Light handler not available"

            await self.light_handler.handle_update_light(
                username=username,
                data={
                    "command": "update_light",
                    "light_name": light_name,
                    "color": color
                },
                client_type="agent"
            )

            return f"Updated {light_name} color to {color}"

        except Exception as e:
            self.logger.error(f"Error updating light color: {str(e)}")
            return f"Error updating light color: {str(e)}"

    async def update_light_strength(self, username: str, light_name: str, strength: int) -> str:
        """Update the strength/intensity of a specific light"""
        try:
            if not self.light_handler:
                return "Light handler not available"

            await self.light_handler.handle_update_light(
                username=username,
                data={
                    "command": "update_light",
                    "light_name": light_name,
                    "strength": strength
                },
                client_type="agent"
            )

            return f"Updated {light_name} strength to {strength}"

        except Exception as e:
            self.logger.error(f"Error updating light strength: {str(e)}")
            return f"Error updating light strength: {str(e)}"

    async def update_light_properties(self, username: str, light_name: str,
                                      color: Optional[str] = None,
                                      strength: Optional[int] = None) -> str:
        """Update multiple properties of a light at once"""
        try:
            if not self.light_handler:
                return "Light handler not available"

            data = {
                "command": "update_light",
                "light_name": light_name
            }

            if color:
                data["color"] = color
            if strength is not None:
                data["strength"] = strength

            await self.light_handler.handle_update_light(
                username=username,
                data=data,
                client_type="agent"
            )

            updates = []
            if color:
                updates.append(f"color to {color}")
            if strength is not None:
                updates.append(f"strength to {strength}")

            return f"Updated {light_name}: {', '.join(updates)}"

        except Exception as e:
            self.logger.error(f"Error updating light properties: {str(e)}")
            return f"Error updating light properties: {str(e)}"

    async def update_material_color(self, username: str, material_name: str, color: str) -> str:
        """Update the color of a specific material"""
        try:
            if not self.material_handler:
                return "Material handler not available"

            await self.material_handler.handle_update_material(
                username=username,
                data={
                    "command": "update_material",
                    "material_name": material_name,
                    "color": color
                },
                client_type="agent"
            )

            return f"Updated {material_name} color to {color}"

        except Exception as e:
            self.logger.error(f"Error updating material color: {str(e)}")
            return f"Error updating material color: {str(e)}"

    async def transform_object(self, username: str, object_name: str,
                               location: Optional[Dict[str, float]] = None,
                               rotation: Optional[Dict[str, float]] = None,
                               scale: Optional[Dict[str, float]] = None) -> str:
        """Transform an object (move, rotate, or scale)"""
        try:
            if not self.object_handler:
                return "Object handler not available"

            data = {
                "command": "update_object",
                "object_name": object_name
            }

            if location:
                data["location"] = location
            if rotation:
                data["rotation"] = rotation
            if scale:
                data["scale"] = scale

            await self.object_handler.handle_update_object(
                username=username,
                data=data,
                client_type="agent"
            )

            transforms = []
            if location:
                transforms.append("moved")
            if rotation:
                transforms.append("rotated")
            if scale:
                transforms.append("scaled")

            return f"Transformed {object_name}: {', '.join(transforms)}"

        except Exception as e:
            self.logger.error(f"Error transforming object: {str(e)}")
            return f"Error transforming object: {str(e)}"
