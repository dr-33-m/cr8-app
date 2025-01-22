from typing import List, Optional
from sqlmodel import SQLModel, Field, Column, Relationship, String, ARRAY
from .user import User
from datetime import datetime


class Moodboard(SQLModel, table=True):
    id: int = Field(primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="moodboards")
    name: str
    description: str
    storyline: str = None
    keywords: List[str] = Field(sa_column=Column(ARRAY(String)))
    industry: str = None
    targetAudience: str = None
    theme: str = None
    tone: str = None
    videoReferences: List[str] = Field(sa_column=Column(ARRAY(String)))
    colorPalette: List[str] = Field(sa_column=Column(ARRAY(String)))
    usage_intent: str = None

    # Moodboard Images
    images: List["MoodboardImage"] = Relationship(back_populates="moodboard")
    projects: List["Project"] = Relationship(back_populates="moodboard")

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class MoodboardImage(SQLModel, table=True):
    id: int = Field(primary_key=True)
    moodboard_id: int = Field(foreign_key="moodboard.id")
    file: str  # Path or URL
    annotation: Optional[str] = None
    category: str  # e.g., compositions, actions, lighting, location
    moodboard: Moodboard = Relationship(back_populates="images")
