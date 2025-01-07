from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from ..schemas.user import UserRead  # Assuming UserRead is defined in user.py


class TemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    minio_path: str
    price: Optional[float] = None
    is_public: bool = False
    template_controls: Dict[str, Any] = {}


class TemplateCreate(TemplateBase):
    creator_id: int  # Include here since it's necessary during creation.


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    minio_path: Optional[str] = None
    price: Optional[float] = None
    is_public: Optional[bool] = None
    # Explicit None default.
    template_controls: Optional[Dict[str, Any]] = None


class TemplateRead(TemplateBase):
    id: int
    creator: UserRead
    # Replace with more descriptive types if needed.
    project_templates: List[int] = []

    class Config:
        orm_mode = True
