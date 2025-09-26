import httpx
import logging
from typing import Dict, List, Optional, Union, Any
from fastapi import HTTPException
from app.models.polyhaven import (
    Asset, HDRI, Texture, Model, Author,
    HDRIFiles, TextureFiles, ModelFiles,
    File, OptionalFile, FileWithIncludes
)

logger = logging.getLogger(__name__)


class PolyHavenService:
    """Service for interacting with the Poly Haven API"""
    
    BASE_URL = "https://api.polyhaven.com"
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "CR8-PolyHaven-Integration/1.0"
            }
        )
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Make an HTTP request to the Poly Haven API with error handling"""
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            logger.info(f"Making request to Poly Haven API: {url} with params: {params}")
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        
        except httpx.TimeoutException:
            logger.error(f"Timeout when requesting {url}")
            raise HTTPException(
                status_code=504,
                detail="Request to Poly Haven API timed out"
            )
        
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} when requesting {url}: {e.response.text}")
            if e.response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail="Asset not found"
                )
            elif e.response.status_code == 400:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid request parameters"
                )
            else:
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"Poly Haven API error: {e.response.text}"
                )
        
        except httpx.RequestError as e:
            logger.error(f"Request error when accessing {url}: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail="Unable to connect to Poly Haven API"
            )
        
        except Exception as e:
            logger.error(f"Unexpected error when requesting {url}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Internal server error while accessing Poly Haven API"
            )
    
    async def get_asset_types(self) -> List[str]:
        """Get list of available asset types"""
        data = await self._make_request("/types")
        return data
    
    async def get_assets(self, asset_type: Optional[str] = None, categories: Optional[str] = None) -> Dict[str, Any]:
        """Get list of assets with optional filtering"""
        params = {}
        if asset_type:
            params["type"] = asset_type
        if categories:
            params["categories"] = categories
        
        data = await self._make_request("/assets", params)
        return data
    
    async def get_asset_info(self, asset_id: str) -> Union[HDRI, Texture, Model]:
        """Get detailed information about a specific asset"""
        data = await self._make_request(f"/info/{asset_id}")
        
        # Determine asset type and return appropriate model
        asset_type = data.get("type")
        if asset_type == 0:  # HDRI
            return HDRI(**data)
        elif asset_type == 1:  # Texture
            return Texture(**data)
        elif asset_type == 2:  # Model
            return Model(**data)
        else:
            # Fallback to base Asset model
            return Asset(**data)
    
    async def get_asset_files(self, asset_id: str) -> Union[HDRIFiles, TextureFiles, ModelFiles]:
        """Get file information for a specific asset"""
        data = await self._make_request(f"/files/{asset_id}")
        
        # Try to determine asset type from the file structure
        if "hdri" in data:
            return self._parse_hdri_files(data)
        elif any(key in data for key in ["blend", "gltf", "fbx", "usd"]) and any(key.endswith(("_diff", "_diffuse", "_col", "_color", "_albedo", "_normal", "_rough", "_roughness", "_metal", "_metallic", "_ao", "_disp", "_displacement", "_bump", "_height", "_spec", "_specular")) for key in data.keys()):
            # Check if it has model-specific formats or texture maps
            if any(key in data for key in ["fbx", "usd"]):
                return self._parse_model_files(data)
            else:
                return self._parse_texture_files(data)
        else:
            # Default to texture files if structure is ambiguous
            return self._parse_texture_files(data)
    
    def _parse_hdri_files(self, data: Dict[str, Any]) -> HDRIFiles:
        """Parse HDRI file structure"""
        hdri_files = {}
        backplates = None
        colorchart = None
        tonemapped = None
        
        # Parse HDRI files
        if "hdri" in data:
            hdri_files = self._parse_file_dict(data["hdri"])
        
        # Parse optional files
        if "backplates" in data and data["backplates"]:
            backplates = self._parse_file_dict(data["backplates"])
        
        if "colorchart" in data and data["colorchart"]:
            colorchart = OptionalFile(**data["colorchart"])
        
        if "tonemapped" in data and data["tonemapped"]:
            tonemapped = OptionalFile(**data["tonemapped"])
        
        return HDRIFiles(
            hdri=hdri_files,
            backplates=backplates,
            colorchart=colorchart,
            tonemapped=tonemapped
        )
    
    def _parse_texture_files(self, data: Dict[str, Any]) -> TextureFiles:
        """Parse texture file structure"""
        texture_files = TextureFiles()
        
        # Parse known file types
        if "blend" in data:
            texture_files.blend = self._parse_file_dict_with_includes(data["blend"])
        
        if "gltf" in data:
            texture_files.gltf = self._parse_file_dict_with_includes(data["gltf"])
        
        if "mtlx" in data:
            texture_files.mtlx = self._parse_file_dict_with_includes(data["mtlx"])
        
        # Parse texture maps (any key that doesn't match known file types)
        maps = {}
        for key, value in data.items():
            if key not in ["blend", "gltf", "mtlx"] and isinstance(value, dict):
                maps[key] = self._parse_file_dict(value)
        
        if maps:
            texture_files.maps = maps
        
        return texture_files
    
    def _parse_model_files(self, data: Dict[str, Any]) -> ModelFiles:
        """Parse model file structure"""
        model_files = ModelFiles()
        
        # Parse known file types
        if "blend" in data:
            model_files.blend = self._parse_file_dict_with_includes(data["blend"])
        
        if "gltf" in data:
            model_files.gltf = self._parse_file_dict_with_includes(data["gltf"])
        
        if "fbx" in data:
            model_files.fbx = self._parse_file_dict_with_includes(data["fbx"])
        
        if "usd" in data:
            model_files.usd = self._parse_file_dict_with_includes(data["usd"])
        
        # Parse texture maps (any key that doesn't match known file types)
        maps = {}
        for key, value in data.items():
            if key not in ["blend", "gltf", "fbx", "usd"] and isinstance(value, dict):
                maps[key] = self._parse_file_dict(value)
        
        if maps:
            model_files.maps = maps
        
        return model_files
    
    def _parse_file_dict(self, file_data: Dict[str, Any]) -> Dict[str, Dict[str, File]]:
        """Parse a nested file dictionary structure"""
        result = {}
        for resolution, formats in file_data.items():
            if isinstance(formats, dict):
                result[resolution] = {}
                for format_name, file_info in formats.items():
                    if isinstance(file_info, dict) and all(key in file_info for key in ["url", "md5", "size"]):
                        result[resolution][format_name] = File(**file_info)
        return result
    
    def _parse_file_dict_with_includes(self, file_data: Dict[str, Any]) -> Dict[str, Dict[str, FileWithIncludes]]:
        """Parse a nested file dictionary structure with includes"""
        result = {}
        for resolution, formats in file_data.items():
            if isinstance(formats, dict):
                result[resolution] = {}
                for format_name, file_info in formats.items():
                    if isinstance(file_info, dict) and all(key in file_info for key in ["url", "md5", "size"]):
                        # Parse include files if present
                        includes = None
                        if "include" in file_info and file_info["include"]:
                            includes = {}
                            for include_path, include_info in file_info["include"].items():
                                if isinstance(include_info, dict):
                                    includes[include_path] = File(**include_info)
                        
                        result[resolution][format_name] = FileWithIncludes(
                            url=file_info["url"],
                            md5=file_info["md5"],
                            size=file_info["size"],
                            include=includes
                        )
        return result
    
    async def get_author_info(self, author_id: str) -> Author:
        """Get information about a specific author"""
        data = await self._make_request(f"/author/{author_id}")
        return Author(**data)
    
    async def get_categories(self, asset_type: str, in_categories: Optional[str] = None) -> Dict[str, int]:
        """Get categories for a specific asset type"""
        params = {}
        if in_categories:
            params["in"] = in_categories
        
        data = await self._make_request(f"/categories/{asset_type}", params)
        return data


# Global service instance
polyhaven_service = PolyHavenService()


async def get_polyhaven_service() -> PolyHavenService:
    """Dependency injection for the Poly Haven service"""
    return polyhaven_service
