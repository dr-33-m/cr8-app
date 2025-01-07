from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class AssetBase(BaseModel):
    id: Optional[int]
    name: str
    description: Optional[str]
    asset_type: Optional[str]
    minio_path: str
    creator_id: int
    price: Optional[float]
    is_public: bool = False
    controls: Dict[str, Any] = {}

    class Config:
        orm_mode = True


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    asset_type: Optional[str]
    minio_path: Optional[str]
    price: Optional[float]
    is_public: Optional[bool]
    controls: Optional[Dict[str, Any]]

    class Config:
        orm_mode = True


class AssetRead(AssetBase):
    pass


class FavoriteBase(BaseModel):
    id: Optional[int]
    user_id: int
    asset_id: Optional[int]
    template_id: Optional[int]

    class Config:
        orm_mode = True


class FavoriteCreate(FavoriteBase):
    pass


class FavoriteUpdate(BaseModel):
    asset_id: Optional[int]
    template_id: Optional[int]

    class Config:
        orm_mode = True


class FavoriteRead(FavoriteBase):
    pass
