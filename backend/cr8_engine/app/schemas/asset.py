from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class AssetBase(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    asset_type: Optional[str] = None
    minio_path: str
    creator_id: int
    price: Optional[float] = None
    is_public: bool = False
    controls: Dict[str, Any] = {}

    class Config:
        orm_mode = True


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    asset_type: Optional[str] = None
    minio_path: Optional[str] = None
    price: Optional[float] = None
    is_public: Optional[bool] = None
    controls: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True


class AssetRead(AssetBase):
    pass


class FavoriteBase(BaseModel):
    id: Optional[int] = None
    user_id: int
    asset_id: Optional[int] = None
    template_id: Optional[int] = None

    class Config:
        orm_mode = True


class FavoriteCreate(FavoriteBase):
    pass


class FavoriteUpdate(BaseModel):
    asset_id: Optional[int] = None
    template_id: Optional[int] = None

    class Config:
        orm_mode = True


class FavoriteRead(FavoriteBase):
    pass
