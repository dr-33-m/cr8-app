"""
Registry implementations for multi-registry asset system.

Provides modular registry implementations for different asset sources:
- Polyhaven: Free high-quality PBR assets
- BlenderKit: Premium community assets (future)
"""

from .polyhaven import PolyhavenRegistry

__all__ = ["PolyhavenRegistry"]
