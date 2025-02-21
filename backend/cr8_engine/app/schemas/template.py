from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
from ..schemas.user import UserRead


class TemplateBase(BaseModel):
    name: str
    template_type: str
    templateData: Dict[str, Any] = Field(default_factory=dict)
    thumbnail: Optional[str] = None
    compatible_templates: Optional[List[int]] = Field(default_factory=list)
    is_public: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TemplateCreate(TemplateBase):
    creator_id: int
    templateData: Dict[str, Any] = Field(default_factory=dict)


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    template_type: Optional[str] = None
    templateData: Optional[Dict[str, Any]] = None
    thumbnail: Optional[str] = None
    compatible_templates: Optional[List[int]] = None
    is_public: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TemplateRead(TemplateBase):
    id: int
    creator_id: int
    project_templates: List[int] = Field(default_factory=list)

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
