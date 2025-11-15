"""
Polyhaven asset download coordination and handlers.

Manages downloading assets from Polyhaven API and coordinating imports.
"""

import os
import tempfile
import shutil
import requests
import logging
from typing import Dict, Any, Optional, Tuple
from contextlib import suppress

from ...registry_base import AssetType, DownloadResult
from . import importers

logger = logging.getLogger(__name__)


def download_asset(base_url: str,
                  asset_id: str,
                  resolution: str = "1k",
                  file_format: Optional[str] = None,
                  import_to_scene: bool = True,
                  location: Optional[Tuple[float, float, float]] = None) -> DownloadResult:
    """
    Download Polyhaven asset using proven blender-mcp implementation
    
    Args:
        base_url: Polyhaven API base URL
        asset_id: Polyhaven asset ID
        resolution: Asset resolution (1k, 2k, 4k, 8k, etc.)
        file_format: Specific file format (hdr, exr, jpg, png, etc.)
        import_to_scene: Whether to import to Blender scene
        location: 3D location for asset placement
        
    Returns:
        DownloadResult with success status and details
    """
    try:
        # Get asset info first to determine type
        asset_info = _get_asset_info(base_url, asset_id)
        if not asset_info:
            return DownloadResult(
                success=False,
                message=f"Could not get asset info for {asset_id}"
            )
        
        asset_type_int = asset_info.get("type", 1)
        if asset_type_int == 0:
            asset_type = "hdris"
        elif asset_type_int == 1:
            asset_type = "textures"
        elif asset_type_int == 2:
            asset_type = "models"
        else:
            return DownloadResult(
                success=False,
                message=f"Unsupported asset type: {asset_type_int}"
            )
        
        # Get files information
        files_response = requests.get(f"{base_url}/files/{asset_id}", timeout=30)
        if files_response.status_code != 200:
            return DownloadResult(
                success=False,
                message=f"Failed to get asset files: {files_response.status_code}"
            )
        
        files_data = files_response.json()
        asset_name = asset_info.get("name", asset_id)
        
        # Handle different asset types using proven blender-mcp code
        if asset_type == "hdris":
            return _download_hdri(asset_id, asset_name, files_data, resolution, file_format, import_to_scene)
        elif asset_type == "textures":
            return _download_texture(asset_id, asset_name, files_data, resolution, file_format, import_to_scene, location)
        elif asset_type == "models":
            return _download_model(asset_id, asset_name, files_data, resolution, file_format, import_to_scene, location)
        else:
            return DownloadResult(
                success=False,
                message=f"Unsupported asset type: {asset_type}"
            )
            
    except Exception as e:
        logger.error(f"Polyhaven download failed: {e}")
        return DownloadResult(
            success=False,
            message=f"Download failed: {str(e)}",
            error_details=str(e)
        )


def _get_asset_info(base_url: str, asset_id: str) -> Dict[str, Any]:
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


def _download_hdri(asset_id: str, asset_name: str, files_data: Dict, 
                  resolution: str, file_format: Optional[str], import_to_scene: bool) -> DownloadResult:
    """Download and import HDRI using proven blender-mcp code"""
    try:
        if not file_format:
            file_format = "hdr"  # Default format for HDRIs
        
        if "hdri" in files_data and resolution in files_data["hdri"] and file_format in files_data["hdri"][resolution]:
            file_info = files_data["hdri"][resolution][file_format]
            file_url = file_info["url"]
            
            # Download to temporary file
            with tempfile.NamedTemporaryFile(suffix=f".{file_format}", delete=False) as tmp_file:
                response = requests.get(file_url, timeout=60)
                if response.status_code != 200:
                    return DownloadResult(
                        success=False,
                        message=f"Failed to download HDRI: {response.status_code}"
                    )
                
                tmp_file.write(response.content)
                tmp_path = tmp_file.name
            
            if import_to_scene:
                import_result = importers.import_hdri_to_scene(tmp_path, asset_name, file_format)
                return DownloadResult(
                    success=import_result["success"],
                    message=import_result["message"],
                    file_path=tmp_path,
                    asset_name=asset_name,
                    asset_type=AssetType.HDRI,
                    imported=import_result["success"]
                )
            else:
                return DownloadResult(
                    success=True,
                    message=f"HDRI {asset_name} downloaded successfully",
                    file_path=tmp_path,
                    asset_name=asset_name,
                    asset_type=AssetType.HDRI,
                    imported=False
                )
        else:
            return DownloadResult(
                success=False,
                message=f"Requested resolution or format not available for this HDRI"
            )
            
    except Exception as e:
        return DownloadResult(
            success=False,
            message=f"Failed to download HDRI: {str(e)}",
            error_details=str(e)
        )


def _download_texture(asset_id: str, asset_name: str, files_data: Dict,
                     resolution: str, file_format: Optional[str], import_to_scene: bool,
                     location: Optional[Tuple[float, float, float]]) -> DownloadResult:
    """Download and import texture using proven blender-mcp code"""
    try:
        if not file_format:
            file_format = "jpg"  # Default format for textures
        
        downloaded_maps = {}
        
        # Download all available texture maps
        for map_type in files_data:
            if map_type not in ["blend", "gltf"]:  # Skip non-texture files
                if resolution in files_data[map_type] and file_format in files_data[map_type][resolution]:
                    file_info = files_data[map_type][resolution][file_format]
                    file_url = file_info["url"]
                    
                    # Download to temporary file
                    with tempfile.NamedTemporaryFile(suffix=f".{file_format}", delete=False) as tmp_file:
                        response = requests.get(file_url, timeout=60)
                        if response.status_code == 200:
                            tmp_file.write(response.content)
                            downloaded_maps[map_type] = tmp_file.name
        
        if not downloaded_maps:
            return DownloadResult(
                success=False,
                message=f"No texture maps found for the requested resolution and format"
            )
        
        if import_to_scene:
            import_result = importers.import_texture_to_scene(asset_id, asset_name, downloaded_maps)
            
            # Clean up temporary files
            for tmp_path in downloaded_maps.values():
                with suppress(Exception):
                    os.unlink(tmp_path)
            
            return DownloadResult(
                success=import_result["success"],
                message=import_result["message"],
                asset_name=asset_name,
                asset_type=AssetType.TEXTURE,
                imported=import_result["success"],
                imported_objects=[import_result.get("material", "")]
            )
        else:
            return DownloadResult(
                success=True,
                message=f"Texture {asset_name} downloaded successfully",
                asset_name=asset_name,
                asset_type=AssetType.TEXTURE,
                imported=False
            )
            
    except Exception as e:
        return DownloadResult(
            success=False,
            message=f"Failed to download texture: {str(e)}",
            error_details=str(e)
        )


def _download_model(asset_id: str, asset_name: str, files_data: Dict,
                   resolution: str, file_format: Optional[str], import_to_scene: bool,
                   location: Optional[Tuple[float, float, float]]) -> DownloadResult:
    """Download and import model using proven blender-mcp code"""
    try:
        if not file_format:
            file_format = "gltf"  # Default format for models
        
        if file_format in files_data and resolution in files_data[file_format]:
            file_info = files_data[file_format][resolution][file_format]
            file_url = file_info["url"]
            
            # Create temporary directory for model and dependencies
            temp_dir = tempfile.mkdtemp()
            main_file_path = ""
            
            try:
                # Download main model file
                main_file_name = file_url.split("/")[-1]
                main_file_path = os.path.join(temp_dir, main_file_name)
                
                response = requests.get(file_url, timeout=60)
                if response.status_code != 200:
                    return DownloadResult(
                        success=False,
                        message=f"Failed to download model: {response.status_code}"
                    )
                
                with open(main_file_path, "wb") as f:
                    f.write(response.content)
                
                # Download dependencies if any
                if "include" in file_info and file_info["include"]:
                    for include_path, include_info in file_info["include"].items():
                        include_url = include_info["url"]
                        include_file_path = os.path.join(temp_dir, include_path)
                        os.makedirs(os.path.dirname(include_file_path), exist_ok=True)
                        
                        include_response = requests.get(include_url, timeout=60)
                        if include_response.status_code == 200:
                            with open(include_file_path, "wb") as f:
                                f.write(include_response.content)
                
                if import_to_scene:
                    import_result = importers.import_model_to_scene(main_file_path, asset_name, file_format, location)
                    
                    # Clean up temporary directory
                    with suppress(Exception):
                        shutil.rmtree(temp_dir)
                    
                    return DownloadResult(
                        success=import_result["success"],
                        message=import_result["message"],
                        asset_name=asset_name,
                        asset_type=AssetType.MODEL,
                        imported=import_result["success"],
                        imported_objects=import_result.get("imported_objects", [])
                    )
                else:
                    return DownloadResult(
                        success=True,
                        message=f"Model {asset_name} downloaded successfully",
                        file_path=main_file_path,
                        asset_name=asset_name,
                        asset_type=AssetType.MODEL,
                        imported=False
                    )
                    
            except Exception as e:
                # Clean up on error
                with suppress(Exception):
                    shutil.rmtree(temp_dir)
                return DownloadResult(
                    success=False,
                    message=f"Failed to process model: {str(e)}"
                )
        else:
            return DownloadResult(
                success=False,
                message=f"Requested format or resolution not available for this model"
            )
            
    except Exception as e:
        return DownloadResult(
            success=False,
            message=f"Failed to download model: {str(e)}",
            error_details=str(e)
        )
