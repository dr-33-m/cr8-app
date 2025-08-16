"""
Context Manager for B.L.A.Z.E Agent
Maintains awareness of current scene state and available controls.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SceneContext:
    """Current scene context information"""
    username: str
    available_cameras: List[Dict[str, Any]]
    available_lights: List[Dict[str, Any]]
    available_materials: List[Dict[str, Any]]
    available_objects: List[Dict[str, Any]]
    placed_assets: List[Dict[str, Any]]
    current_camera: Optional[str] = None

    def get_summary(self) -> str:
        """Get a human-readable summary of the scene"""
        summary_parts = []

        if self.available_cameras:
            camera_names = [cam.get('name', '')
                            for cam in self.available_cameras]
            summary_parts.append(f"Cameras: {', '.join(camera_names)}")

        if self.available_lights:
            light_names = [light.get('name', '')
                           for light in self.available_lights]
            summary_parts.append(f"Lights: {', '.join(light_names)}")

        if self.available_materials:
            material_names = [mat.get('name', '')
                              for mat in self.available_materials]
            summary_parts.append(f"Materials: {', '.join(material_names)}")

        if self.available_objects:
            object_names = [obj.get('name', '')
                            for obj in self.available_objects]
            summary_parts.append(f"Objects: {', '.join(object_names)}")

        if self.placed_assets:
            asset_names = [asset.get('name', '')
                           for asset in self.placed_assets]
            summary_parts.append(f"Assets: {', '.join(asset_names)}")

        if self.current_camera:
            summary_parts.append(f"Current camera: {self.current_camera}")

        return "; ".join(summary_parts) if summary_parts else "No scene elements available"


class ContextManager:
    """Manages scene context for B.L.A.Z.E agent"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ContextManager, cls).__new__(cls)
            cls._instance._contexts = {}
            cls._instance.logger = logging.getLogger(__name__)
            cls._instance.logger.info(
                "ContextManager singleton instance created")
        return cls._instance

    def __init__(self):
        # No-op for singleton
        pass

    def get_context(self, username: str) -> Optional[SceneContext]:
        """Get scene context for a user"""
        return self._contexts.get(username)

    def create_context(self, username: str) -> SceneContext:
        """Create initial context for a user"""
        context = SceneContext(
            username=username,
            available_cameras=[],
            available_lights=[],
            available_materials=[],
            available_objects=[],
            placed_assets=[]
        )
        self._contexts[username] = context
        self.logger.info(f"Created scene context for user {username}")
        return context

    def update_template_controls(self, username: str, template_controls: Dict[str, Any]) -> None:
        """Update template controls in context"""
        context = self._contexts.get(username)
        if not context:
            context = self.create_context(username)

        context.available_cameras = template_controls.get('cameras', [])
        context.available_lights = template_controls.get('lights', [])
        context.available_materials = template_controls.get('materials', [])
        context.available_objects = template_controls.get('objects', [])

        # Debug logging
        self.logger.info(f"Updated template controls for user {username}")
        self.logger.info(f"Cameras: {len(context.available_cameras)}")
        self.logger.info(f"Lights: {len(context.available_lights)}")
        self.logger.info(f"Materials: {len(context.available_materials)}")
        self.logger.info(f"Objects: {len(context.available_objects)}")
        for cam in context.available_cameras:
            self.logger.info(
                f"Camera: {cam.get('displayName', cam.get('name', 'Unknown'))}")
        for light in context.available_lights:
            self.logger.info(
                f"Light: {light.get('displayName', light.get('name', 'Unknown'))}")

    def update_placed_assets(self, username: str, assets: List[Dict[str, Any]]) -> None:
        """Update placed assets in context"""
        context = self._contexts.get(username)
        if not context:
            context = self.create_context(username)

        context.placed_assets = assets
        self.logger.info(
            f"Updated placed assets for user {username}: {len(assets)} assets")

    def set_current_camera(self, username: str, camera_name: str) -> None:
        """Set the current camera"""
        context = self._contexts.get(username)
        if not context:
            context = self.create_context(username)

        context.current_camera = camera_name
        self.logger.info(
            f"Set current camera for user {username}: {camera_name}")

    def clear_context(self, username: str) -> None:
        """Clear context for a user"""
        if username in self._contexts:
            del self._contexts[username]
            self.logger.info(f"Cleared context for user {username}")

    def get_scene_summary(self, username: str) -> str:
        """Get scene summary for agent context"""
        self.logger.info(f"Getting scene summary for user: {username}")
        self.logger.info(f"Available contexts: {list(self._contexts.keys())}")

        context = self.get_context(username)
        if not context:
            self.logger.warning(f"No context found for user {username}")
            return "No scene context available"

        summary = context.get_summary()
        self.logger.info(f"Scene summary for {username}: {summary}")
        return summary
