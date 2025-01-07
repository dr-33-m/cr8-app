from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from ..models.constants import UserRole, SubscriptionTier

# Pydantic model for User


class UserBase(BaseModel):
    logto_id: str = Field(..., description="Logto authentication ID")
    email: str = Field(..., description="User's email address")
    username: str = Field(..., description="User's username")
    role: Optional[str] = Field(
        default=UserRole.CONTENT_CREATOR, description="User's role")
    subscription_tier: Optional[str] = Field(
        default=SubscriptionTier.BASIC, description="User's subscription tier")
    subscription_active: bool = Field(
        default=True, description="Whether the subscription is active")
    revenue_share: Optional[float] = Field(
        default=0.0, description="Revenue share percentage")

# Pydantic model for creating a User


class UserCreate(UserBase):
    pass

# Pydantic model for updating a User


class UserUpdate(BaseModel):
    email: Optional[str] = Field(None, description="User's email address")
    username: Optional[str] = Field(None, description="User's username")
    role: Optional[str] = Field(None, description="User's role")
    subscription_tier: Optional[str] = Field(
        None, description="User's subscription tier")
    subscription_active: Optional[bool] = Field(
        None, description="Whether the subscription is active")
    revenue_share: Optional[float] = Field(
        None, description="Revenue share percentage")

# Pydantic model for reading a User (includes relationships)


class UserRead(UserBase):
    id: int = Field(..., description="User's unique identifier")
    projects: List["Project"] = Field(
        [], description="List of projects associated with the user")
    favorites: List["Favorite"] = Field(
        [], description="List of favorites associated with the user")
    created_assets: List["Asset"] = Field(
        [], description="List of assets created by the user")
    created_templates: List["Template"] = Field(
        [], description="List of templates created by the user")
    moodboards: List["Moodboard"] = Field(
        [], description="List of moodboards associated with the user")

    class Config:
        orm_mode = True
