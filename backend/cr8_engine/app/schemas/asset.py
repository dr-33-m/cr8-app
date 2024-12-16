from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from ..models import AssetType


class AssetBase(BaseModel):
    name: str
    description: Optional[str] = None
    type: AssetType
    minio_path: str
    price: Optional[float] = None
    is_public: bool = False
    controls: Dict[str, Any] = {}


class AssetCreate(AssetBase):
    creator_id: int


class AssetRead(AssetBase):
    id: int
    creator_id: int

    class Config:
        orm_mode = True


class AssetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[AssetType] = None
    minio_path: Optional[str] = None
    price: Optional[float] = None
    is_public: Optional[bool] = None
    controls: Optional[Dict[str, Any]] = None


class FavoriteBase(BaseModel):
    user_id: int
    asset_id: Optional[int] = None
    template_id: Optional[int] = None


class FavoriteCreate(FavoriteBase):
    pass


class FavoriteRead(FavoriteBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
