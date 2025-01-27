from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship, Column
from datetime import datetime
from .constants import UserRole, SubscriptionTier


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    logto_id: str = Field(unique=True, index=True)  # Logto authentication ID
    email: str = Field(unique=True, index=True)
    username: str
    role: Optional[str] = Field(default=UserRole.CONTENT_CREATOR)

    # Content Creator Specific Fields
    subscription_tier: Optional[str] = Field(default=SubscriptionTier.BASIC)
    subscription_active: bool = Field(default=True)

    # Relationships
    projects: List["Project"] = Relationship(back_populates="user")
    favorites: List["Favorite"] = Relationship(back_populates="user")

    # CG Artist Specific Fields
    created_assets: List["Asset"] = Relationship(back_populates="creator")
    created_templates: List["Template"] = Relationship(
        back_populates="creator")
    revenue_share: Optional[float] = Field(default=0.0)
    moodboards: List["Moodboard"] = Relationship(back_populates="user")
