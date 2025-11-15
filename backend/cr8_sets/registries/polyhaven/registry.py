"""
Polyhaven Registry Implementation - Orchestrator

Main registry class that coordinates search, download, and import operations.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple

from ...registry_base import (
    AssetRegistry, 
    RegistryType, 
    AssetType, 
    StandardizedAsset, 
    DownloadResult
)
from . import search, downloaders, texture_utils

logger = logging.getLogger(__name__)


class PolyhavenRegistry(AssetRegistry):
    """Polyhaven asset registry implementation"""
    
    def __init__(self):
        super().__init__(RegistryType.POLYHAVEN)
        self.base_url = "https://api.polyhaven.com"
        self.authenticated = True  # No auth required for Polyhaven
        
        # Asset type mapping from Polyhaven API to our standard types
        self.polyhaven_to_standard = {
            "hdris": AssetType.HDRI,
            "textures": AssetType.TEXTURE,
            "models": AssetType.MODEL
        }
        
        self.standard_to_polyhaven = {
            AssetType.HDRI: "hdris",
            AssetType.HDR: "hdris",  # Alias
            AssetType.TEXTURE: "textures", 
            AssetType.MATERIAL: "textures",  # Alias
            AssetType.MODEL: "models"
        }
    
    def authenticate(self, **kwargs) -> bool:
        """Polyhaven doesn't require authentication"""
        self.authenticated = True
        return True
    
    def get_supported_asset_types(self) -> List[AssetType]:
        """Get supported asset types for Polyhaven"""
        return [AssetType.HDRI, AssetType.TEXTURE, AssetType.MODEL]
    
    def search_assets(self, 
                     query: str, 
                     asset_type: Optional[AssetType] = None,
                     limit: int = 10,
                     categories: Optional[str] = None,
                     **kwargs) -> List[StandardizedAsset]:
        """
        Search Polyhaven assets using the working blender-mcp implementation
        
        Args:
            query: Search query (used for filtering by tags/names)
            asset_type: Type of asset to search for
            limit: Maximum number of results
            categories: Comma-separated category filter
            **kwargs: Additional parameters
            
        Returns:
            List of standardized assets
        """
        return search.search_assets(
            base_url=self.base_url,
            query=query,
            asset_type=asset_type,
            limit=limit,
            categories=categories,
            standard_to_polyhaven=self.standard_to_polyhaven
        )
    
    def get_asset_details(self, asset_id: str) -> Dict[str, Any]:
        """Get detailed information about a Polyhaven asset"""
        return search.get_asset_details(self.base_url, asset_id)
    
    def get_categories(self, asset_type: Optional[AssetType] = None) -> List[str]:
        """Get available categories for Polyhaven assets"""
        return search.get_categories(
            base_url=self.base_url,
            asset_type=asset_type,
            standard_to_polyhaven=self.standard_to_polyhaven
        )
    
    def download_asset(self, 
                      asset_id: str,
                      resolution: str = "1k",
                      file_format: Optional[str] = None,
                      import_to_scene: bool = True,
                      location: Optional[Tuple[float, float, float]] = None,
                      **kwargs) -> DownloadResult:
        """
        Download Polyhaven asset using proven blender-mcp implementation
        
        Args:
            asset_id: Polyhaven asset ID
            resolution: Asset resolution (1k, 2k, 4k, 8k, etc.)
            file_format: Specific file format (hdr, exr, jpg, png, etc.)
            import_to_scene: Whether to import to Blender scene
            location: 3D location for asset placement
            **kwargs: Additional parameters
            
        Returns:
            DownloadResult with success status and details
        """
        return downloaders.download_asset(
            base_url=self.base_url,
            asset_id=asset_id,
            resolution=resolution,
            file_format=file_format,
            import_to_scene=import_to_scene,
            location=location
        )
    
    def apply_texture_to_object(self, object_name: str, texture_asset_id: str) -> Dict[str, Any]:
        """Apply a previously downloaded Polyhaven texture to a specific object"""
        return texture_utils.apply_texture_to_object(object_name, texture_asset_id)
