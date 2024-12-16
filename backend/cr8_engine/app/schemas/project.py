from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

from ..models import ProjectStatus


class ProjectBase(BaseModel):
    name: str
    status: ProjectStatus


class ProjectCreate(ProjectBase):
    user_id: int


class ProjectRead(ProjectBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[ProjectStatus] = None
