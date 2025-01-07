from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class MoodboardBase(BaseModel):
    user_id: int
    name: str
    description: str
    storyline: str
    keywords: List[str]
    industry: Optional[str] = None
    targetAudience: str
    theme: Optional[str] = None
    tone: Optional[str] = None
    videoReferences: List[str]
    colorPalette: List[str]
    usage_intent: Optional[str] = None

    class Config:
        orm_mode = True


class MoodboardCreate(MoodboardBase):
    pass


class MoodboardUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    storyline: Optional[str]
    keywords: Optional[List[str]]
    industry: Optional[str]
    targetAudience: Optional[str]
    theme: Optional[str]
    tone: Optional[str]
    videoReferences: Optional[List[str]]
    colorPalette: Optional[List[str]]
    usage_intent: Optional[str]

    class Config:
        orm_mode = True


class MoodboardRead(MoodboardBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class MoodboardImageBase(BaseModel):
    moodboard_id: int
    file: str
    annotation: Optional[str] = None
    category: str  # e.g., compositions, actions, lighting, location

    class Config:
        orm_mode = True


class MoodboardImageCreate(MoodboardImageBase):
    pass


class MoodboardImageUpdate(BaseModel):
    file: Optional[str] = None
    annotation: Optional[str] = None
    category: Optional[str] = None

    class Config:
        orm_mode = True


class MoodboardImageRead(MoodboardImageBase):
    id: int

    class Config:
        orm_mode = True
