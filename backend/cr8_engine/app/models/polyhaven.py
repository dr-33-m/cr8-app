from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field


# Base file models
class File(BaseModel):
    url: str = Field(description="Direct URL to download this file")
    md5: str = Field(description="MD5 checksum for verifying file integrity")
    size: int = Field(description="Size of the file in bytes")


class OptionalFile(BaseModel):
    url: str = Field(description="Direct URL to download this file")
    md5: str = Field(description="MD5 checksum for verifying file integrity")
    size: int = Field(description="Size of the file in bytes")


class FileWithIncludes(BaseModel):
    url: str = Field(description="Direct URL to download this file")
    md5: str = Field(description="MD5 checksum for verifying file integrity")
    size: int = Field(description="Size of the file in bytes")
    include: Optional[Dict[str, File]] = Field(
        default=None,
        description="A list of files that this file depends on and should be included when downloaded"
    )


# Author model
class Author(BaseModel):
    name: str = Field(description="The author's full name, which may be different from the ID")
    link: Optional[str] = Field(default=None, description="The author's preferred link to their portfolio")
    email: Optional[str] = Field(default=None, description="Email address of the author")
    donate: Optional[str] = Field(
        default=None,
        description="Donation info of this author. May be a link to a donation page, or an email prefixed with 'paypal:'"
    )


# Base asset model
class Asset(BaseModel):
    name: str = Field(description="The human-readable/display name")
    type: int = Field(description="The asset type. HDRIs = 0, textures = 1, models = 2")
    date_published: int = Field(description="The epoch timestamp in seconds of when this asset was published")
    download_count: int = Field(description="The number of times this asset was downloaded")
    files_hash: str = Field(description="A SHA1 hash of the files object, which will change whenever the files are updated")
    authors: Dict[str, str] = Field(description="Who created this asset, and what they did")
    donated: Optional[bool] = Field(default=None, description="Whether or not this asset was donated free of charge")
    categories: List[str] = Field(description="A string array of categories that this asset belongs to")
    tags: List[str] = Field(description="A string array of tags for this asset to help with search matches")
    max_resolution: List[int] = Field(description="The highest resolution available for this asset, in pixels")
    thumbnail_url: str = Field(description="The URL of the preview image thumbnail for this asset")


# Specific asset type models
class HDRI(Asset):
    whitebalance: Optional[int] = Field(
        default=None,
        description="The whitebalance in Kelvin that this HDRI and any included backplates were shot at"
    )
    backplates: Optional[bool] = Field(default=None, description="Whether there are backplates available for this HDRI")
    evs_cap: int = Field(
        description="The number of exposure brackets captured when shooting this HDRI"
    )
    coords: Optional[List[float]] = Field(default=None, description="Decimal lat/lon GPS coordinates")
    date_taken: Optional[int] = Field(
        default=None,
        description="Legacy epoch timestamp of when this HDRI was taken",
        deprecated=True
    )


class Texture(Asset):
    dimensions: List[int] = Field(description="An array with the dimensions of this asset on each axis in millimeters")


class Model(Asset):
    lods: Optional[List[int]] = Field(default=None, description="A list of LOD triangle counts in order")


# File structure models for different asset types
class HDRIFiles(BaseModel):
    hdri: Dict[str, Dict[str, File]] = Field(description="HDRI files organized by resolution and format")
    backplates: Optional[Dict[str, Dict[str, File]]] = Field(default=None, description="Backplate images if available")
    colorchart: Optional[OptionalFile] = Field(default=None, description="Color chart file if available")
    tonemapped: Optional[OptionalFile] = Field(default=None, description="Tonemapped preview if available")


class TextureFiles(BaseModel):
    blend: Optional[Dict[str, Dict[str, FileWithIncludes]]] = Field(default=None, description="Blend files by resolution")
    gltf: Optional[Dict[str, Dict[str, FileWithIncludes]]] = Field(default=None, description="glTF files by resolution")
    mtlx: Optional[Dict[str, Dict[str, FileWithIncludes]]] = Field(default=None, description="MaterialX files by resolution")
    # Dynamic texture map fields (e.g., diffuse, normal, roughness, etc.)
    # Using Dict[str, Any] to handle dynamic map types
    maps: Optional[Dict[str, Dict[str, Dict[str, File]]]] = Field(default=None, description="Texture maps by type, resolution, and format")

    class Config:
        extra = "allow"  # Allow additional fields for dynamic texture maps


class ModelFiles(BaseModel):
    blend: Optional[Dict[str, Dict[str, FileWithIncludes]]] = Field(default=None, description="Blend files by resolution")
    gltf: Optional[Dict[str, Dict[str, FileWithIncludes]]] = Field(default=None, description="glTF files by resolution")
    fbx: Optional[Dict[str, Dict[str, FileWithIncludes]]] = Field(default=None, description="FBX files by resolution")
    usd: Optional[Dict[str, Dict[str, FileWithIncludes]]] = Field(default=None, description="USD files by resolution")
    # Dynamic texture map fields for model textures
    maps: Optional[Dict[str, Dict[str, Dict[str, File]]]] = Field(default=None, description="Texture maps by type, resolution, and format")

    class Config:
        extra = "allow"  # Allow additional fields for dynamic texture maps


# Response models for API endpoints
class AssetTypesResponse(BaseModel):
    types: List[str] = Field(description="Array of asset types", example=["hdris", "textures", "models"])


class AssetsResponse(BaseModel):
    assets: Dict[str, Asset] = Field(description="Dictionary of assets keyed by asset ID")


class AssetInfoResponse(BaseModel):
    asset: Union[HDRI, Texture, Model] = Field(description="Detailed asset information")


class AssetFilesResponse(BaseModel):
    files: Union[HDRIFiles, TextureFiles, ModelFiles] = Field(description="File information for the asset")


class CategoriesResponse(BaseModel):
    categories: Dict[str, int] = Field(description="Categories with asset counts")


# Request models
class AssetsRequest(BaseModel):
    type: Optional[str] = Field(default=None, description="Filter to assets of a particular type")
    categories: Optional[str] = Field(default=None, description="Comma-separated list of categories to filter by")


class CategoriesRequest(BaseModel):
    type: str = Field(description="Asset type to get categories for")
    in_categories: Optional[str] = Field(default=None, alias="in", description="Comma separated list of categories to filter by")
