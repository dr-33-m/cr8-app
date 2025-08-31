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
    current_objects: List[str]
    last_updated: Optional[str] = None

    def get_summary(self) -> str:
        """Get a human-readable summary of the scene"""
        if self.current_objects:
            return f"Scene objects: {', '.join(self.current_objects)}"
        else:
            return "Empty scene"


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
            current_objects=[]
        )
        self._contexts[username] = context
        self.logger.info(f"Created scene context for user {username}")
        return context

    def update_scene_objects(self, username: str, objects_list: List[str]) -> None:
        """Update scene objects from live scene query"""
        import datetime
        
        context = self._contexts.get(username)
        if not context:
            context = self.create_context(username)

        context.current_objects = objects_list
        context.last_updated = datetime.datetime.now().isoformat()
        
        self.logger.info(f"Updated scene objects for user {username}: {len(objects_list)} objects")
        self.logger.debug(f"Scene objects: {', '.join(objects_list)}")

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
