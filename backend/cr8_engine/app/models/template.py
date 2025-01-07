from typing import Optional, Dict, Any, List
from sqlmodel import SQLModel, Field, Relationship, Column, JSON
from .user import User


class Template(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    minio_path: str  # Path to template in MinIO storage

    creator_id: int = Field(foreign_key="user.id")
    creator: User = Relationship(back_populates="created_templates")

    price: Optional[float] = None
    is_public: bool = Field(default=False)

    # Scalable template controls
    template_controls: Dict[str, Any] = Field(
        sa_column=Column(JSON), default_factory=dict)

    # Relationships
    project_templates: List["ProjectTemplate"] = Relationship(
        back_populates="template")
