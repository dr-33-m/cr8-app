"""
Multi-Registry Base Classes for Asset Management
==============================================

Provides abstract base classes and interfaces for implementing different
asset registries (Polyhaven, BlenderKit, etc.) in a unified system.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum


class AssetType(Enum):
    """Standardized asset types across registries"""
    MODEL = "model"
    MATERIAL = "material" 
    TEXTURE = "texture"
    HDRI = "hdri"
    HDR = "hdri"  # Alias for HDRI
    BRUSH = "brush"
    SCENE = "scene"


class RegistryType(Enum):
    """Supported asset registries"""
    POLYHAVEN = "polyhaven"
    BLENDERKIT = "blenderkit"
    SKETCHFAB = "sketchfab"


@dataclass
class StandardizedAsset:
    """Standardized asset metadata format across all registries"""
    id: str
    name: str
    asset_type: AssetType
    registry: RegistryType
    thumbnail_url: str
    tags: List[str]
    categories: List[str]
    download_count: int = 0
    quality_score: float = 0.0
    rating: float = 0.0
    file_size: int = 0
    resolution: Optional[Tuple[int, int]] = None
    author: Optional[str] = None
    description: Optional[str] = ""
    date_published: Optional[int] = None
    download_info: Optional[Dict[str, Any]] = None
    raw_data: Optional[Dict[str, Any]] = None  # Original registry-specific data


@dataclass
class DownloadResult:
    """Result of asset download operation"""
    success: bool
    message: str
    file_path: Optional[str] = None
    asset_name: Optional[str] = None
    asset_type: Optional[AssetType] = None
    imported: bool = False
    imported_objects: Optional[List[str]] = None
    error_details: Optional[str] = None


class AssetRegistry(ABC):
    """Abstract base class for asset registries"""
    
    def __init__(self, registry_type: RegistryType):
        self.registry_type = registry_type
        self.base_url = ""
        self.authenticated = False
    
    @abstractmethod
    def search_assets(self, 
                     query: str, 
                     asset_type: Optional[AssetType] = None,
                     limit: int = 10,
                     **kwargs) -> List[StandardizedAsset]:
        """
        Search for assets using natural language query
        
        Args:
            query: Natural language search query
            asset_type: Type of asset to search for
            limit: Maximum number of results
            **kwargs: Registry-specific parameters
            
        Returns:
            List of standardized assets
        """
        pass
    
    @abstractmethod
    def get_asset_details(self, asset_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific asset
        
        Args:
            asset_id: Unique asset identifier
            
        Returns:
            Detailed asset information
        """
        pass
    
    @abstractmethod
    def download_asset(self, 
                      asset_id: str, 
                      download_path: Optional[str] = None,
                      **kwargs) -> DownloadResult:
        """
        Download an asset by ID
        
        Args:
            asset_id: Unique asset identifier
            download_path: Optional specific download path
            **kwargs: Registry-specific download options
            
        Returns:
            Download result with file path and metadata
        """
        pass
    
    @abstractmethod
    def get_categories(self, asset_type: Optional[AssetType] = None) -> List[str]:
        """
        Get available categories for filtering
        
        Args:
            asset_type: Asset type to get categories for
            
        Returns:
            List of available categories
        """
        pass
    
    @abstractmethod
    def authenticate(self, **kwargs) -> bool:
        """
        Authenticate with the registry if required
        
        Args:
            **kwargs: Registry-specific authentication parameters
            
        Returns:
            True if authentication successful
        """
        pass
    
    def is_authenticated(self) -> bool:
        """Check if registry is authenticated and ready"""
        return self.authenticated
    
    def get_registry_info(self) -> Dict[str, Any]:
        """Get information about this registry"""
        return {
            "name": self.registry_type.value,
            "base_url": self.base_url,
            "authenticated": self.authenticated,
            "supported_asset_types": self.get_supported_asset_types()
        }
    
    @abstractmethod
    def get_supported_asset_types(self) -> List[AssetType]:
        """Get list of asset types supported by this registry"""
        pass


class RegistryManager:
    """Manages multiple asset registries"""
    
    def __init__(self):
        self.registries: Dict[RegistryType, AssetRegistry] = {}
        self.default_registry: Optional[RegistryType] = None
    
    def register_registry(self, registry: AssetRegistry):
        """Register a new asset registry"""
        self.registries[registry.registry_type] = registry
        
        # Set as default if it's the first registry
        if self.default_registry is None:
            self.default_registry = registry.registry_type
    
    def get_registry(self, registry_type: RegistryType) -> Optional[AssetRegistry]:
        """Get a specific registry by type"""
        return self.registries.get(registry_type)
    
    def get_available_registries(self) -> List[RegistryType]:
        """Get list of available registry types"""
        return list(self.registries.keys())
    
    def search_assets(self,
                     query: str,
                     registry: Optional[RegistryType] = None,
                     asset_type: Optional[AssetType] = None,
                     limit: int = 10,
                     **kwargs) -> List[StandardizedAsset]:
        """
        Search assets across registries
        
        Args:
            query: Natural language search query
            registry: Specific registry to search (None for default)
            asset_type: Type of asset to search for
            limit: Maximum number of results
            **kwargs: Registry-specific parameters
            
        Returns:
            List of standardized assets
        """
        target_registry = registry or self.default_registry
        
        if target_registry not in self.registries:
            raise ValueError(f"Registry {target_registry} not available")
        
        registry_obj = self.registries[target_registry]
        return registry_obj.search_assets(query, asset_type, limit, **kwargs)
    
    def download_asset(self,
                      asset_id: str,
                      registry: RegistryType,
                      **kwargs) -> DownloadResult:
        """
        Download asset from specific registry
        
        Args:
            asset_id: Asset identifier
            registry: Registry to download from
            **kwargs: Registry-specific download options
            
        Returns:
            Download result
        """
        if registry not in self.registries:
            return DownloadResult(
                success=False,
                message=f"Registry {registry} not available"
            )
        
        registry_obj = self.registries[registry]
        return registry_obj.download_asset(asset_id, **kwargs)


# Global registry manager instance
registry_manager = RegistryManager()
