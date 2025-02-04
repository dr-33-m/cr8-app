from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class MoodboardBase(BaseModel):
    user_id: int
    name: str
    description: str
    storyline: Optional[str] = None
    keywords: List[str] = []  # Default empty list (not Optional)
    industry: Optional[str] = None
    targetAudience: Optional[str] = None
    theme: Optional[str] = None
    tone: Optional[str] = None
    videoReferences: List[str] = []  # Default empty list
    colorPalette: List[str] = []  # Default empty list
    usage_intent: Optional[str] = None

    class Config:
        orm_mode = True


class MoodboardCreate(MoodboardBase):
    pass


class MoodboardUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    storyline: Optional[str] = None
    keywords: Optional[List[str]] = None
    industry: Optional[str] = None
    targetAudience: Optional[str] = None
    theme: Optional[str] = None
    tone: Optional[str] = None
    videoReferences: Optional[List[str]] = None
    colorPalette: Optional[List[str]] = None
    usage_intent: Optional[str] = None

    class Config:
        orm_mode = True


class MoodboardRead(MoodboardBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
