"""
Multi-Registry Asset Manager - AI-Capable Asset Addon
====================================================

A lightweight, fast multi-registry asset addon with AI-powered asset selection,
designed for B.L.A.Z.E integration with support for multiple asset registries.

Features:
- Multi-registry support (Polyhaven, BlenderKit, etc.)
- Direct API calls for fast asset access
- AI-powered asset selection and scoring
- Natural language search interface
- B.L.A.Z.E compatible operators
- Automatic asset import and scene integration

Supported Registries:
- Polyhaven: Free high-quality PBR assets (HDRIs, textures, models)
- BlenderKit: Premium community assets (coming soon)
"""

bl_info = {
    "name": "Multi-Registry Asset Manager", 
    "description": "AI-capable multi-registry asset addon with direct API access for fast asset search across Polyhaven, BlenderKit, and more",
    "author": "Multi-Registry AI Team",
    "version": (2, 0, 0),
    "blender": (3, 0, 0),
    "location": "AI Integration Only",
    "warning": "AI-only addon - no UI panels",
    "doc_url": "https://github.com/your-repo/multi-registry-assets",
    "tracker_url": "https://github.com/your-repo/multi-registry-assets/issues",
    "support": "COMMUNITY",
    "category": "Import-Export",
}

import bpy

# Import our multi-registry modules
from .integration import AI_COMMAND_HANDLERS


# Simple registration for AI-only addon
def register():
    """Register addon (AI-only, no UI components)"""
    # Initialize and register Polyhaven registry
    from .registries import PolyhavenRegistry
    from .registry_base import registry_manager
    
    polyhaven = PolyhavenRegistry()
    registry_manager.register_registry(polyhaven)
    
    print("Multi-Registry Asset Manager registered successfully")
    print(f"Available registries: {[r.value for r in registry_manager.get_available_registries()]}")


def unregister():
    """Unregister addon"""
    print("Multi-Registry Asset Manager unregistered")


# Export AI command handlers for B.L.A.Z.E/CR8 orchestrator discovery
# Import the complete set from integration.blaze.registry (includes asset + spatial tools)

if __name__ == "__main__":
    register()
