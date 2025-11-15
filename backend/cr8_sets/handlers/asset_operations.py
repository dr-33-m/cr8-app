"""
Registry-agnostic asset operations handler.

Provides core asset operations that work with any registry through the
RegistryManager abstraction. All operations work on StandardizedAsset format.
"""

import logging
from typing import Dict, List, Optional, Any

from ..registry_base import (
    AssetType,
    RegistryType,
    registry_manager,
    StandardizedAsset,
)
from .scoring import score_and_rank_assets

logger = logging.getLogger(__name__)


def search_assets(
    query: str,
    registry_type: Optional[RegistryType] = None,
    asset_type: Optional[AssetType] = None,
    limit: int = 10,
    categories: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Search for assets across registries using natural language.
    
    Registry-agnostic: Works with any registry via RegistryManager.
    
    Args:
        query: Natural language search query
        registry_type: Registry to search (None for default)
        asset_type: Type of asset to search for
        limit: Maximum number of results
        categories: Comma-separated category filter
        **kwargs: Additional registry-specific parameters
        
    Returns:
        Dictionary with search results and metadata
    """
    try:
        logger.info(f"Searching for '{query}' (type: {asset_type}, registry: {registry_type})")
        
        # Use registry manager to search (registry-agnostic)
        assets = registry_manager.search_assets(
            query=query,
            registry=registry_type,
            asset_type=asset_type,
            limit=limit,
            categories=categories,
            **kwargs,
        )
        
        if not assets:
            return {
                "success": False,
                "message": f"No assets found for '{query}'",
                "total_count": 0,
                "assets": [],
            }
        
        # Score and rank assets (works on StandardizedAsset)
        scored_assets = score_and_rank_assets(assets, query)
        
        # Format results
        formatted_assets = [_format_asset(asset) for asset in scored_assets]
        
        return {
            "success": True,
            "message": f"Found {len(formatted_assets)} assets for '{query}'",
            "total_count": len(formatted_assets),
            "returned_count": len(formatted_assets),
            "assets": formatted_assets,
            "query": query,
            "asset_type": asset_type.value if asset_type else None,
            "registry": registry_type.value if registry_type else None,
        }
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return {
            "success": False,
            "message": f"Search failed: {str(e)}",
            "total_count": 0,
            "assets": [],
        }


def download_asset(
    asset_id: str,
    registry_type: RegistryType,
    import_to_scene: bool = True,
    location: Optional[tuple] = None,
    resolution: str = "1k",
    file_format: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Download asset from specified registry.
    
    Registry-agnostic: Works with any registry via RegistryManager.
    
    Args:
        asset_id: Asset identifier
        registry_type: Registry to download from
        import_to_scene: Whether to import to Blender scene
        location: (x, y, z) tuple for placement
        resolution: Asset resolution
        file_format: Specific file format
        **kwargs: Additional registry-specific parameters
        
    Returns:
        Dictionary with download results
    """
    try:
        logger.info(f"Downloading asset {asset_id} from {registry_type.value}")
        
        # Use registry manager to download (registry-agnostic)
        result = registry_manager.download_asset(
            asset_id=asset_id,
            registry=registry_type,
            import_to_scene=import_to_scene,
            location=location,
            resolution=resolution,
            file_format=file_format,
            **kwargs,
        )
        
        # Format result
        return {
            "success": result.success,
            "message": result.message,
            "asset_id": asset_id,
            "asset_name": result.asset_name,
            "asset_type": result.asset_type.value if result.asset_type else None,
            "registry": registry_type.value,
            "file_path": result.file_path,
            "imported": result.imported,
            "imported_objects": result.imported_objects or [],
            "error_details": result.error_details,
        }
        
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return {
            "success": False,
            "message": f"Download failed: {str(e)}",
            "asset_id": asset_id,
            "registry": registry_type.value,
        }


def get_categories(
    registry_type: Optional[RegistryType] = None,
    asset_type: Optional[AssetType] = None,
) -> Dict[str, Any]:
    """
    Get available categories for a registry.
    
    Registry-agnostic: Works with any registry via RegistryManager.
    
    Args:
        registry_type: Registry to get categories from (None for default)
        asset_type: Asset type to filter categories
        
    Returns:
        Dictionary with categories list
    """
    try:
        target_registry = registry_type or registry_manager.default_registry
        
        if target_registry not in registry_manager.registries:
            return {
                "success": False,
                "message": f"Registry {target_registry} not available",
                "categories": [],
            }
        
        registry_obj = registry_manager.get_registry(target_registry)
        categories = registry_obj.get_categories(asset_type)
        
        return {
            "success": True,
            "categories": categories,
            "registry": target_registry.value,
            "asset_type": asset_type.value if asset_type else None,
            "count": len(categories),
        }
        
    except Exception as e:
        logger.error(f"Get categories failed: {e}")
        return {
            "success": False,
            "message": f"Failed to get categories: {str(e)}",
            "categories": [],
        }


def apply_texture_to_object(
    object_name: str,
    texture_asset_id: str,
    registry_type: RegistryType,
) -> Dict[str, Any]:
    """
    Apply a texture to a specific object.
    
    Registry-agnostic: Works with any registry that supports texture application.
    
    Args:
        object_name: Name of the Blender object
        texture_asset_id: Asset ID of the texture
        registry_type: Registry the texture came from
        
    Returns:
        Dictionary with operation results
    """
    try:
        if registry_type not in registry_manager.registries:
            return {
                "success": False,
                "message": f"Registry {registry_type} not available",
            }
        
        registry_obj = registry_manager.get_registry(registry_type)
        
        # Check if registry supports texture application
        if not hasattr(registry_obj, "apply_texture_to_object"):
            return {
                "success": False,
                "message": f"Texture application not supported for {registry_type.value}",
            }
        
        result = registry_obj.apply_texture_to_object(object_name, texture_asset_id)
        
        if "error" in result:
            return {
                "success": False,
                "message": result["error"],
            }
        
        return {
            "success": result.get("success", True),
            "message": result.get("message", "Texture applied successfully"),
            "material": result.get("material"),
            "maps": result.get("maps", []),
        }
        
    except Exception as e:
        logger.error(f"Apply texture failed: {e}")
        return {
            "success": False,
            "message": f"Failed to apply texture: {str(e)}",
        }


def find_and_add_asset(
    query: str,
    registry_type: RegistryType,
    asset_type: Optional[AssetType] = None,
    location: Optional[tuple] = None,
    resolution: str = "1k",
) -> Dict[str, Any]:
    """
    Complete workflow: search, select best match, download, and add to scene.
    
    Registry-agnostic: Works with any registry.
    
    Args:
        query: Natural language description of desired asset
        registry_type: Registry to search
        asset_type: Type of asset
        location: (x, y, z) tuple for placement
        resolution: Asset resolution
        
    Returns:
        Dictionary with complete operation results
    """
    try:
        logger.info(f"Find and add request: '{query}' (type: {asset_type}, registry: {registry_type.value})")
        
        # Search for assets
        search_result = search_assets(
            query=query,
            registry_type=registry_type,
            asset_type=asset_type,
            limit=5,
        )
        
        if not search_result["success"] or not search_result["assets"]:
            return {
                "success": False,
                "message": f"No suitable assets found for '{query}'",
                "search_result": search_result,
            }
        
        # Get the best asset (first in sorted list)
        best_asset = search_result["assets"][0]
        asset_id = best_asset["id"]
        asset_name = best_asset["name"]
        
        logger.info(f"Selected best asset: {asset_name} (ID: {asset_id})")
        
        # Download the asset
        download_result = download_asset(
            asset_id=asset_id,
            registry_type=registry_type,
            import_to_scene=True,
            location=location,
            resolution=resolution,
        )
        
        return {
            "success": download_result["success"],
            "message": download_result.get("message", "Processing completed"),
            "search_result": search_result,
            "download_result": download_result,
            "selected_asset": {
                "id": asset_id,
                "name": asset_name,
                "type": asset_type.value if asset_type else None,
                "registry": registry_type.value,
                "score": best_asset.get("score"),
            },
        }
        
    except Exception as e:
        logger.error(f"Find and add failed: {e}")
        return {
            "success": False,
            "message": f"Operation failed: {str(e)}",
        }


def _format_asset(asset: StandardizedAsset) -> Dict[str, Any]:
    """
    Format a StandardizedAsset for API response.
    
    Works with any registry since it operates on the standardized format.
    """
    return {
        "id": asset.id,
        "name": asset.name,
        "description": asset.description,
        "registry": asset.registry.value,
        "asset_type": asset.asset_type.value,
        "thumbnail_url": asset.thumbnail_url,
        "tags": asset.tags,
        "categories": asset.categories,
        "download_count": asset.download_count,
        "quality_score": asset.quality_score,
        "rating": asset.rating,
        "author": asset.author,
        "resolution": asset.resolution,
        "score": {
            "total": asset.quality_score + asset.rating / 2,
            "quality": asset.quality_score,
            "popularity": min(asset.download_count / 10000, 1.0),
            "rating": asset.rating,
        },
    }
