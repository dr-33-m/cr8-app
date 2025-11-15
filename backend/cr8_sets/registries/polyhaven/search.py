"""
Polyhaven search and metadata operations.

Handles asset searching, filtering, and metadata retrieval from Polyhaven API.
"""

import requests
import logging
from typing import Dict, List, Optional, Any

from ...registry_base import AssetType, RegistryType, StandardizedAsset

logger = logging.getLogger(__name__)


def search_assets(base_url: str,
                 query: str,
                 asset_type: Optional[AssetType] = None,
                 limit: int = 10,
                 categories: Optional[str] = None,
                 standard_to_polyhaven: Dict[AssetType, str] = None) -> List[StandardizedAsset]:
    """
    Search Polyhaven assets using the working blender-mcp implementation
    
    Args:
        base_url: Polyhaven API base URL
        query: Search query (used for filtering by tags/names)
        asset_type: Type of asset to search for
        limit: Maximum number of results
        categories: Comma-separated category filter
        standard_to_polyhaven: Mapping from standard types to Polyhaven types
        
    Returns:
        List of standardized assets
    """
    try:
        if standard_to_polyhaven is None:
            standard_to_polyhaven = {
                AssetType.HDRI: "hdris",
                AssetType.HDR: "hdris",
                AssetType.TEXTURE: "textures",
                AssetType.MATERIAL: "textures",
                AssetType.MODEL: "models"
            }
        
        # Convert asset type to Polyhaven format
        polyhaven_type = None
        if asset_type:
            polyhaven_type = standard_to_polyhaven.get(asset_type)
            if not polyhaven_type:
                logger.warning(f"Unsupported asset type for Polyhaven: {asset_type}")
                return []
        
        # Build API request
        url = f"{base_url}/assets"
        params = {}
        
        if polyhaven_type:
            params["type"] = polyhaven_type
        
        if categories:
            params["categories"] = categories
        
        # Make request to Polyhaven API
        response = requests.get(url, params=params, timeout=30)
        if response.status_code != 200:
            logger.error(f"Polyhaven API request failed: {response.status_code}")
            return []
        
        assets_data = response.json()
        
        # Convert to standardized format
        standardized_assets = []
        query_lower = query.lower() if query else ""
        
        for asset_id, asset_data in assets_data.items():
            # Filter by query if provided (search in name and tags)
            if query:
                asset_name = asset_data.get("name", "").lower()
                asset_tags = [tag.lower() for tag in asset_data.get("tags", [])]
                asset_categories = [cat.lower() for cat in asset_data.get("categories", [])]
                
                # Check if query matches name, tags, or categories
                query_words = query_lower.split()
                matches = any(
                    word in asset_name or 
                    any(word in tag for tag in asset_tags) or
                    any(word in cat for cat in asset_categories)
                    for word in query_words
                )
                
                if not matches:
                    continue
            
            # Convert Polyhaven asset type to standard type
            polyhaven_asset_type = asset_data.get("type", 1)  # Default to texture
            if polyhaven_asset_type == 0:
                std_asset_type = AssetType.HDRI
            elif polyhaven_asset_type == 1:
                std_asset_type = AssetType.TEXTURE
            elif polyhaven_asset_type == 2:
                std_asset_type = AssetType.MODEL
            else:
                continue  # Unknown type
            
            # Get resolution info
            max_res = asset_data.get("max_resolution", [0, 0])
            resolution = (max_res[0], max_res[1]) if len(max_res) >= 2 else None
            
            # Get author info
            authors = asset_data.get("authors", {})
            author = list(authors.keys())[0] if authors else None
            
            # Create standardized asset
            standardized_asset = StandardizedAsset(
                id=asset_id,
                name=asset_data.get("name", asset_id),
                asset_type=std_asset_type,
                registry=RegistryType.POLYHAVEN,
                thumbnail_url=asset_data.get("thumbnail_url", ""),
                tags=asset_data.get("tags", []),
                categories=asset_data.get("categories", []),
                download_count=asset_data.get("download_count", 0),
                quality_score=0.8,  # Polyhaven assets are generally high quality
                rating=0.9,  # Polyhaven assets are curated and high quality
                resolution=resolution,
                author=author,
                date_published=asset_data.get("date_published"),
                raw_data=asset_data
            )
            
            standardized_assets.append(standardized_asset)
            
            # Limit results
            if len(standardized_assets) >= limit:
                break
        
        # Sort by relevance (simple scoring based on query match)
        if query:
            standardized_assets.sort(key=lambda asset: _calculate_relevance(asset, query_lower), reverse=True)
        
        logger.info(f"Found {len(standardized_assets)} Polyhaven assets for query: {query}")
        return standardized_assets[:limit]
        
    except Exception as e:
        logger.error(f"Polyhaven search failed: {e}")
        return []


def get_asset_details(base_url: str, asset_id: str) -> Dict[str, Any]:
    """Get detailed information about a Polyhaven asset"""
    try:
        response = requests.get(f"{base_url}/info/{asset_id}", timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to get Polyhaven asset details: {response.status_code}")
            return {}
    except Exception as e:
        logger.error(f"Error getting Polyhaven asset details: {e}")
        return {}


def get_categories(base_url: str,
                  asset_type: Optional[AssetType] = None,
                  standard_to_polyhaven: Dict[AssetType, str] = None) -> List[str]:
    """Get available categories for Polyhaven assets"""
    try:
        if standard_to_polyhaven is None:
            standard_to_polyhaven = {
                AssetType.HDRI: "hdris",
                AssetType.HDR: "hdris",
                AssetType.TEXTURE: "textures",
                AssetType.MATERIAL: "textures",
                AssetType.MODEL: "models"
            }
        
        # Convert to Polyhaven asset type
        polyhaven_type = "all"
        if asset_type:
            polyhaven_type = standard_to_polyhaven.get(asset_type, "all")
        
        response = requests.get(f"{base_url}/categories/{polyhaven_type}", timeout=30)
        if response.status_code == 200:
            categories_data = response.json()
            return list(categories_data.keys())
        else:
            logger.error(f"Failed to get Polyhaven categories: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Error getting Polyhaven categories: {e}")
        return []


def _calculate_relevance(asset: StandardizedAsset, query_lower: str) -> float:
    """Calculate relevance score for an asset based on query"""
    if not query_lower:
        return 0.5
    
    score = 0.0
    query_words = query_lower.split()
    asset_name = asset.name.lower()
    
    # Name exact match gets highest score
    if query_lower in asset_name:
        score += 1.0
    
    # Tag matches
    for tag in asset.tags:
        for word in query_words:
            if word in tag.lower():
                score += 0.5
    
    # Category matches
    for cat in asset.categories:
        for word in query_words:
            if word in cat.lower():
                score += 0.3
    
    return min(score, 1.0)  # Cap at 1.0
