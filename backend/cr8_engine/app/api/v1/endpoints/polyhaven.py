from typing import Dict, List, Optional, Union, Any
from fastapi import APIRouter, Depends, Query, Path
from app.services.polyhaven_service import PolyHavenService, get_polyhaven_service
from app.models.polyhaven import (
    AssetTypesResponse, AssetsResponse, AssetInfoResponse, AssetFilesResponse,
    CategoriesResponse, Author, HDRI, Texture, Model,
    HDRIFiles, TextureFiles, ModelFiles
)

router = APIRouter()


@router.get("/types", response_model=AssetTypesResponse, tags=["polyhaven"])
async def get_asset_types(
    service: PolyHavenService = Depends(get_polyhaven_service)
):
    """
    Get list of available asset types from Poly Haven.
    
    Returns an array of asset types: hdris, textures, models.
    """
    types = await service.get_asset_types()
    return AssetTypesResponse(types=types)


@router.get("/assets", response_model=Dict[str, Any], tags=["polyhaven"])
async def get_assets(
    asset_type: Optional[str] = Query(
        None, 
        alias="type",
        description="Filter to assets of a particular type. Can be hdris/textures/models/all.",
        example="textures"
    ),
    categories: Optional[str] = Query(
        None,
        description="A comma-separated list of categories to filter by. Only assets that match all categories specified will be included.",
        example="brick"
    ),
    service: PolyHavenService = Depends(get_polyhaven_service)
):
    """
    Get a list of assets from Poly Haven, including their individual metadata.
    
    To filter the returned data, optional query parameters can be provided:
    - type: Filter to assets of a particular type
    - categories: Comma-separated list of categories to filter by
    """
    assets = await service.get_assets(asset_type=asset_type, categories=categories)
    return assets


@router.get("/assets/{asset_id}/info", response_model=Union[HDRI, Texture, Model], tags=["polyhaven"])
async def get_asset_info(
    asset_id: str = Path(..., description="The unique ID/slug of the asset", example="abandoned_factory_canteen_01"),
    service: PolyHavenService = Depends(get_polyhaven_service)
):
    """
    Get detailed information about an individual asset specified by its unique ID.
    
    Returns asset metadata including name, type, download count, authors, categories, tags, and more.
    The response type will be HDRI, Texture, or Model depending on the asset type.
    """
    asset_info = await service.get_asset_info(asset_id)
    return asset_info


@router.get("/assets/{asset_id}/files", response_model=Union[HDRIFiles, TextureFiles, ModelFiles], tags=["polyhaven"])
async def get_asset_files(
    asset_id: str = Path(..., description="The unique ID/slug of the asset", example="ceramic_vase_03"),
    service: PolyHavenService = Depends(get_polyhaven_service)
):
    """
    Get file list for a specific asset.
    
    Many files are available for each asset, most of which are available in different resolutions 
    and file formats. This endpoint provides a tree containing all the available files organized 
    by resolution and file type.
    """
    files = await service.get_asset_files(asset_id)
    return files


@router.get("/authors/{author_id}", response_model=Author, tags=["polyhaven"])
async def get_author_info(
    author_id: str = Path(..., description="The unique ID of the author", example="Andreas Mischok"),
    service: PolyHavenService = Depends(get_polyhaven_service)
):
    """
    Get information about a specific author.
    
    Returns data about the requested author, such as their name (which may be different from the ID), 
    links, email (if available), etc.
    """
    author = await service.get_author_info(author_id)
    return author


@router.get("/categories/{asset_type}", response_model=Dict[str, int], tags=["polyhaven"])
async def get_categories(
    asset_type: str = Path(
        ..., 
        description="One of the supported asset types: hdris, textures, or models.",
        example="hdris"
    ),
    in_categories: Optional[str] = Query(
        None,
        alias="in",
        description="A comma separated list of categories - only returns categories with assets that are also in these categories.",
        example="night,clear"
    ),
    service: PolyHavenService = Depends(get_polyhaven_service)
):
    """
    Get a list of available categories for a specific asset type.
    
    The list of categories also shows the number of assets inside them. If 'all' is passed as the 
    asset_type, then rather than returning categories, it simply returns a list of the asset types 
    instead, with their asset counts.
    
    The 'in' parameter can be used to filter categories - only returns categories with assets that 
    are also in the specified categories.
    """
    categories = await service.get_categories(asset_type, in_categories)
    return categories


# Health check endpoint specifically for Poly Haven integration
@router.get("/health", tags=["polyhaven"])
async def polyhaven_health_check(
    service: PolyHavenService = Depends(get_polyhaven_service)
):
    """
    Health check endpoint to verify Poly Haven API connectivity.
    
    This endpoint attempts to fetch the asset types from Poly Haven API to verify connectivity.
    """
    try:
        types = await service.get_asset_types()
        return {
            "status": "healthy",
            "message": "Poly Haven API is accessible",
            "available_types": types
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Poly Haven API is not accessible: {str(e)}"
        }
