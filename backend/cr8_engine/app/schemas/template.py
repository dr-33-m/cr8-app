from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class TemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    minio_path: str
    price: Optional[float] = None
    is_public: bool = False
    template_controls: Dict[str, Any] = {}


class TemplateCreate(TemplateBase):
    creator_id: int


class TemplateRead(TemplateBase):
    id: int
    creator_id: int

    class Config:
        orm_mode = True


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    minio_path: Optional[str] = None
    price: Optional[float] = None
    is_public: Optional[bool] = None
    template_controls: Optional[Dict[str, Any]] = None
