"""
Asset-related B.L.A.Z.E integration functions.

Provides both Polyhaven-specific functions (backward compatibility) and
generic multi-registry functions for searching, downloading, and managing assets.
"""

import json
import logging
from typing import Optional

from ...handlers import (
    search_assets as handler_search_assets,
    download_asset as handler_download_asset,
    get_categories as handler_get_categories,
    apply_texture_to_object as handler_apply_texture,
)
from ...handlers.asset_operations import find_and_add_asset
from ...utils import string_to_asset_type, string_to_registry_type
from ...registry_base import RegistryType

logger = logging.getLogger(__name__)


# ============================================================================
# Polyhaven-Specific Functions (Backward Compatibility)
# ============================================================================


def search_polyhaven_assets(
    query: str,
    asset_type: str = "model",
    limit: int = 10,
    categories: Optional[str] = None,
) -> str:
    """
    Search Polyhaven for assets using natural language.
    
    Args:
        query: Natural language search query
        asset_type: Type of asset (model, texture, hdri)
        limit: Maximum number of results
        categories: Comma-separated category filter
        
    Returns:
        JSON string with search results
    """
    try:
        asset_type_enum = string_to_asset_type(asset_type)
        result = handler_search_assets(
            query=query,
            registry_type=RegistryType.POLYHAVEN,
            asset_type=asset_type_enum,
            limit=limit,
            categories=categories,
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Polyhaven search failed: {e}")
        return json.dumps({"success": False, "message": f"Search failed: {str(e)}"})


def download_polyhaven_asset(
    asset_id: str,
    import_to_scene: bool = True,
    location_x: float = 0.0,
    location_y: float = 0.0,
    location_z: float = 0.0,
    resolution: str = "1k",
    file_format: Optional[str] = None,
) -> str:
    """
    Download a specific Polyhaven asset by ID.
    
    Args:
        asset_id: Polyhaven asset ID
        import_to_scene: Whether to import to scene
        location_x: X coordinate for placement
        location_y: Y coordinate for placement
        location_z: Z coordinate for placement
        resolution: Asset resolution
        file_format: Specific file format
        
    Returns:
        JSON string with download results
    """
    try:
        location = (location_x, location_y, location_z) if any([location_x, location_y, location_z]) else None
        result = handler_download_asset(
            asset_id=asset_id,
            registry_type=RegistryType.POLYHAVEN,
            import_to_scene=import_to_scene,
            location=location,
            resolution=resolution,
            file_format=file_format,
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Polyhaven download failed: {e}")
        return json.dumps({"success": False, "message": f"Download failed: {str(e)}"})


def find_and_add_polyhaven_asset(
    query: str,
    asset_type: str = "model",
    location_x: float = 0.0,
    location_y: float = 0.0,
    location_z: float = 0.0,
    resolution: str = "1k",
) -> str:
    """
    Find and automatically add the best matching Polyhaven asset to the scene.
    
    Args:
        query: Natural language description
        asset_type: Type of asset
        location_x: X coordinate
        location_y: Y coordinate
        location_z: Z coordinate
        resolution: Asset resolution
        
    Returns:
        JSON string with operation results
    """
    try:
        asset_type_enum = string_to_asset_type(asset_type)
        location = (location_x, location_y, location_z) if any([location_x, location_y, location_z]) else None
        
        result = find_and_add_asset(
            query=query,
            registry_type=RegistryType.POLYHAVEN,
            asset_type=asset_type_enum,
            location=location,
            resolution=resolution,
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Find and add failed: {e}")
        return json.dumps({"success": False, "message": f"Operation failed: {str(e)}"})


def get_polyhaven_categories(asset_type: str = "all") -> str:
    """
    Get available categories for Polyhaven assets.
    
    Args:
        asset_type: Type of asset (model, texture, hdri, all)
        
    Returns:
        JSON string with categories list
    """
    try:
        asset_type_enum = string_to_asset_type(asset_type) if asset_type != "all" else None
        result = handler_get_categories(
            registry_type=RegistryType.POLYHAVEN,
            asset_type=asset_type_enum,
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Get categories failed: {e}")
        return json.dumps({"success": False, "message": f"Failed to get categories: {str(e)}"})


def apply_polyhaven_texture_to_object(object_name: str, texture_asset_id: str) -> str:
    """
    Apply a Polyhaven texture to a specific object.
    
    Args:
        object_name: Name of the Blender object
        texture_asset_id: Polyhaven texture asset ID
        
    Returns:
        JSON string with application results
    """
    try:
        result = handler_apply_texture(
            object_name=object_name,
            texture_asset_id=texture_asset_id,
            registry_type=RegistryType.POLYHAVEN,
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Apply texture failed: {e}")
        return json.dumps({"success": False, "message": f"Failed to apply texture: {str(e)}"})


# ============================================================================
# Generic Multi-Registry Functions
# ============================================================================


def search_assets(
    query: str,
    asset_type: str = "model",
    registry: str = "polyhaven",
    limit: int = 10,
    categories: Optional[str] = None,
) -> str:
    """
    Search for assets across different registries.
    
    Args:
        query: Natural language search query
        asset_type: Type of asset
        registry: Registry to search
        limit: Maximum number of results
        categories: Comma-separated category filter
        
    Returns:
        JSON string with search results
    """
    try:
        asset_type_enum = string_to_asset_type(asset_type)
        registry_type = string_to_registry_type(registry)
        
        if not registry_type:
            return json.dumps({"success": False, "message": f"Unsupported registry: {registry}"})
        
        result = handler_search_assets(
            query=query,
            registry_type=registry_type,
            asset_type=asset_type_enum,
            limit=limit,
            categories=categories,
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return json.dumps({"success": False, "message": f"Search failed: {str(e)}"})


def download_asset(
    asset_id: str,
    registry: str = "polyhaven",
    import_to_scene: bool = True,
    location_x: float = 0.0,
    location_y: float = 0.0,
    location_z: float = 0.0,
    resolution: str = "1k",
    file_format: Optional[str] = None,
) -> str:
    """
    Download asset from any supported registry.
    
    Args:
        asset_id: Asset identifier
        registry: Registry to download from
        import_to_scene: Whether to import to scene
        location_x: X coordinate
        location_y: Y coordinate
        location_z: Z coordinate
        resolution: Asset resolution
        file_format: Specific file format
        
    Returns:
        JSON string with download results
    """
    try:
        registry_type = string_to_registry_type(registry)
        if not registry_type:
            return json.dumps({"success": False, "message": f"Unsupported registry: {registry}"})
        
        location = (location_x, location_y, location_z) if any([location_x, location_y, location_z]) else None
        result = handler_download_asset(
            asset_id=asset_id,
            registry_type=registry_type,
            import_to_scene=import_to_scene,
            location=location,
            resolution=resolution,
            file_format=file_format,
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return json.dumps({"success": False, "message": f"Download failed: {str(e)}"})


def get_categories(registry: str = "polyhaven", asset_type: str = "all") -> str:
    """
    Get available categories for a registry.
    
    Args:
        registry: Registry name
        asset_type: Type of asset (model, texture, hdri, all)
        
    Returns:
        JSON string with categories list
    """
    try:
        registry_type = string_to_registry_type(registry)
        if not registry_type:
            return json.dumps({"success": False, "message": f"Unsupported registry: {registry}"})
        
        asset_type_enum = string_to_asset_type(asset_type) if asset_type != "all" else None
        result = handler_get_categories(
            registry_type=registry_type,
            asset_type=asset_type_enum,
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Get categories failed: {e}")
        return json.dumps({"success": False, "message": f"Failed to get categories: {str(e)}"})
