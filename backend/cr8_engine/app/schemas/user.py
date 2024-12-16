from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

from ..models import UserRole, SubscriptionTier


class UserBase(BaseModel):
    email: EmailStr
    username: str
    role: UserRole


class UserCreate(UserBase):
    logto_id: str
    subscription_tier: Optional[SubscriptionTier] = None
    subscription_active: bool = True
    revenue_share: Optional[float] = 0.0


class UserRead(UserBase):
    id: int
    logto_id: str
    subscription_tier: Optional[SubscriptionTier] = None
    subscription_active: bool = True
    revenue_share: Optional[float] = 0.0

    class Config:
        orm_mode = True


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    role: Optional[UserRole] = None
    subscription_tier: Optional[SubscriptionTier] = None
    subscription_active: Optional[bool] = None
    revenue_share: Optional[float] = None
