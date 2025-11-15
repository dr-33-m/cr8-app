"""
Registry-agnostic inbox batch processing handler.

Processes multiple assets from inbox context, downloading and importing them
in batch. Works with any registry through the RegistryManager abstraction.
"""

import logging
from typing import Dict, List, Optional, Any

from ..registry_base import registry_manager, RegistryType
from .asset_operations import download_asset

logger = logging.getLogger(__name__)


def process_inbox_batch(
    inbox_items: List[Dict[str, Any]],
    resolution: str = "1k",
    import_to_scene: bool = True,
) -> Dict[str, Any]:
    """
    Process and download multiple assets from inbox.
    
    Registry-agnostic: Works with assets from any registry.
    
    Args:
        inbox_items: List of inbox items with id, type, name, registry
        resolution: Asset resolution quality for all downloads
        import_to_scene: Whether to automatically import to scene
        
    Returns:
        Dictionary with batch processing results
    """
    try:
        if not inbox_items or not isinstance(inbox_items, list):
            return {
                "success": False,
                "message": "No inbox items provided for processing",
                "processed_count": 0,
                "failed_count": 0,
                "results": [],
            }
        
        results = []
        processed_count = 0
        failed_count = 0
        
        logger.info(f"Processing {len(inbox_items)} inbox items with resolution {resolution}")
        
        # Process each inbox item
        for item in inbox_items:
            try:
                asset_id = item.get("id")
                asset_type = item.get("type")
                asset_name = item.get("name", asset_id)
                registry_str = item.get("registry", "polyhaven")
                
                if not asset_id:
                    results.append({
                        "asset_id": "unknown",
                        "asset_name": asset_name,
                        "success": False,
                        "message": "Missing asset ID",
                    })
                    failed_count += 1
                    continue
                
                # Convert registry string to enum
                registry_type = _string_to_registry_type(registry_str)
                if not registry_type:
                    results.append({
                        "asset_id": asset_id,
                        "asset_name": asset_name,
                        "success": False,
                        "message": f"Unsupported registry: {registry_str}",
                    })
                    failed_count += 1
                    continue
                
                # Download the asset using registry-agnostic handler
                download_result = download_asset(
                    asset_id=asset_id,
                    registry_type=registry_type,
                    import_to_scene=import_to_scene,
                    resolution=resolution,
                )
                
                results.append({
                    "asset_id": asset_id,
                    "asset_name": asset_name,
                    "asset_type": asset_type,
                    "registry": registry_str,
                    "success": download_result["success"],
                    "message": download_result["message"],
                    "imported": download_result.get("imported", False),
                    "imported_objects": download_result.get("imported_objects", []),
                })
                
                if download_result["success"]:
                    processed_count += 1
                else:
                    failed_count += 1
                    
            except Exception as item_error:
                logger.error(f"Failed to process inbox item: {item_error}")
                results.append({
                    "asset_id": item.get("id", "unknown"),
                    "asset_name": item.get("name", "unknown"),
                    "success": False,
                    "message": f"Failed to process item: {str(item_error)}",
                })
                failed_count += 1
        
        success = failed_count == 0
        message = f"Processed {processed_count} of {len(inbox_items)} inbox items"
        if failed_count > 0:
            message += f" ({failed_count} failed)"
        
        return {
            "success": success,
            "message": message,
            "processed_count": processed_count,
            "failed_count": failed_count,
            "total_count": len(inbox_items),
            "results": results,
            "resolution": resolution,
            "import_to_scene": import_to_scene,
        }
        
    except Exception as e:
        logger.error(f"Process inbox batch failed: {e}")
        return {
            "success": False,
            "message": f"Failed to process inbox assets: {str(e)}",
            "processed_count": 0,
            "failed_count": 0,
            "results": [],
        }


def _string_to_registry_type(registry_str: str) -> Optional[RegistryType]:
    """
    Convert registry string to RegistryType enum.
    
    Args:
        registry_str: Registry name as string
        
    Returns:
        RegistryType enum or None if not found
    """
    registry_mapping = {
        "polyhaven": RegistryType.POLYHAVEN,
        "blenderkit": RegistryType.BLENDERKIT,
        "sketchfab": RegistryType.SKETCHFAB,
    }
    return registry_mapping.get(registry_str.lower())
