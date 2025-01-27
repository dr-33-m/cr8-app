from typing import Optional, Dict, Any, List
from sqlmodel import SQLModel, Field, Relationship, Column, JSON
from .user import User


class Template(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    minio_path: str  # Path to template in MinIO storage
    thumbnail_path: Optional[str] = None  # Path to thumbnail in MinIO storage
    tags: Optional[List[str]] = Field(sa_column=Column(JSON))
    creator_id: int = Field(foreign_key="user.id")
    creator: "User" = Relationship(back_populates="created_templates")

    price: Optional[float] = None
    is_public: bool = Field(default=False)

    # Relationships
    project_templates: List["ProjectTemplate"] = Relationship(
        back_populates="template")
    favorites: List["Favorite"] = Relationship(
        back_populates="template")  # Add this line
