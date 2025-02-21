from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship, Column, JSON
from .user import User


class Template(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    template_type: str
    templateData: Dict[str, Any] = Field(sa_column=Column(JSON))
    thumbnail: str
    compatible_templates: Optional[List[int]] = Field(sa_column=Column(JSON))
    is_public: bool = Field(default=True)
    creator_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    creator: "User" = Relationship(back_populates="created_templates")

    # Relationships
    project_templates: List["ProjectTemplate"] = Relationship(
        back_populates="template")
    favorites: List["Favorite"] = Relationship(
        back_populates="template")
