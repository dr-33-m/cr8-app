from typing import List, Optional
from sqlmodel import SQLModel, Field, Column, Relationship, String, ARRAY
from .user import User
from datetime import datetime


class Moodboard(SQLModel, table=True):
    id: int = Field(primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    user: "User" = Relationship(
        back_populates="moodboards")  # Relationship to User
    name: str
    description: str
    storyline: Optional[str] = None
    keywords: List[str] = Field(sa_column=Column(ARRAY(String)))
    industry: Optional[str] = None
    targetAudience: Optional[str] = None
    theme: Optional[str] = None
    tone: Optional[str] = None
    videoReferences: List[str] = Field(sa_column=Column(ARRAY(String)))
    colorPalette: List[str] = Field(sa_column=Column(ARRAY(String)))
    usage_intent: Optional[str] = None

    # Moodboard Images
    images: List["MoodboardImage"] = Relationship(back_populates="moodboard")

    # Relationship to Project
    project_id: Optional[int] = Field(
        default=None, foreign_key="project.id")  # Foreign key to Project
    project: Optional["Project"] = Relationship(
        back_populates="moodboards")  # Relationship to Project

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class MoodboardImage(SQLModel, table=True):
    id: int = Field(primary_key=True)
    moodboard_id: int = Field(foreign_key="moodboard.id")
    file: str  # Path or URL
    annotation: Optional[str] = None
    category: str  # e.g., compositions, actions, lighting, location
    moodboard: "Moodboard" = Relationship(
        back_populates="images")  # Explicit back_populates
