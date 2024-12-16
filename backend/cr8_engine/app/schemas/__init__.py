from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

# Reuse the enums from models
from ..models import (
    UserRole,
    SubscriptionTier,
    AssetType,
    ProjectStatus
)
