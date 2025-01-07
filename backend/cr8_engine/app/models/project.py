from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship, Column
from datetime import datetime
from .user import User


class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    project_status: Optional[str] = Field(default=None)
    user_id: int = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="projects")

    project_type: Optional[str] = Field(default=None)
    subtype: Optional[str] = Field(default=None)
    description: str

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Project can use multiple assets and templates
    project_assets: List["ProjectAsset"] = Relationship(
        back_populates="project")
    project_templates: List["ProjectTemplate"] = Relationship(
        back_populates="project")

# Junction Tables for Many-to-Many Relationships


class ProjectAsset(SQLModel, table=True):
    project_id: Optional[int] = Field(
        default=None, foreign_key="project.id", primary_key=True
    )
    asset_id: Optional[int] = Field(
        default=None, foreign_key="asset.id", primary_key=True
    )
    project: Project = Relationship(back_populates="project_assets")
    asset: "Asset" = Relationship(back_populates="project_assets")


class ProjectTemplate(SQLModel, table=True):
    project_id: Optional[int] = Field(
        default=None, foreign_key="project.id", primary_key=True
    )
    template_id: Optional[int] = Field(
        default=None, foreign_key="template.id", primary_key=True
    )
    project: Project = Relationship(back_populates="project_templates")
    template: "Template" = Relationship(back_populates="project_templates")
