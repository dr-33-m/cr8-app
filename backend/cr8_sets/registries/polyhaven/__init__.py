"""
Polyhaven Registry Package

Modular implementation of Polyhaven asset registry with separated concerns:
- search.py: Asset search and metadata operations
- downloaders.py: Download coordination and asset-type-specific handlers
- importers.py: Blender scene import functions
- texture_utils.py: Texture application utilities
- registry.py: Main orchestrator class
"""

from .registry import PolyhavenRegistry

__all__ = ["PolyhavenRegistry"]
