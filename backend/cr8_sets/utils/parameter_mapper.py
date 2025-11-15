"""
Parameter mapping utilities for multi-registry system.

Converts string parameters to enum types for registry-agnostic operations.
"""

from typing import Optional
from ..registry_base import AssetType, RegistryType


def string_to_asset_type(asset_type_str: Optional[str]) -> Optional[AssetType]:
    """
    Convert asset type string to AssetType enum.
    
    Args:
        asset_type_str: Asset type as string (e.g., "model", "texture", "hdri")
        
    Returns:
        AssetType enum or None if not found
    """
    if not asset_type_str:
        return None
    
    type_mapping = {
        "model": AssetType.MODEL,
        "texture": AssetType.TEXTURE,
        "material": AssetType.TEXTURE,  # Alias
        "hdri": AssetType.HDRI,
        "hdr": AssetType.HDRI,  # Alias
        "brush": AssetType.BRUSH,
        "scene": AssetType.SCENE,
    }
    
    return type_mapping.get(asset_type_str.lower())


def string_to_registry_type(registry_str: Optional[str]) -> Optional[RegistryType]:
    """
    Convert registry string to RegistryType enum.
    
    Args:
        registry_str: Registry name as string (e.g., "polyhaven", "blenderkit")
        
    Returns:
        RegistryType enum or None if not found
    """
    if not registry_str:
        return None
    
    registry_mapping = {
        "polyhaven": RegistryType.POLYHAVEN,
        "blenderkit": RegistryType.BLENDERKIT,
        "sketchfab": RegistryType.SKETCHFAB,
    }
    
    return registry_mapping.get(registry_str.lower())
