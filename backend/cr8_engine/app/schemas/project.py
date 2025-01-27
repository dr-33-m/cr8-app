from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from ..schemas.user import UserRead  # Assuming UserRead is defined in user.py
from ..schemas.asset import AssetRead  # Assuming AssetRead is defined
from ..schemas.template import TemplateRead  # Assuming TemplateRead is defined


class ProjectBase(BaseModel):
    name: str
    project_status: Optional[str] = None
    project_type: Optional[str] = None
    subtype: Optional[str] = None
    description: str


class ProjectCreate(ProjectBase):
    user_id: int


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    project_status: Optional[str] = None
    project_type: Optional[str] = None
    subtype: Optional[str] = None
    description: Optional[str] = None


class ProjectRead(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime
    user: "UserRead"  # Detailed user information
    assets: List["AssetRead"] = []  # Detailed asset information
    templates: List["TemplateRead"] = []  # Detailed template information

    class Config:
        orm_mode = True
