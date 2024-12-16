from .template import Template
from .asset import Asset, Favorite
from .project import Project, ProjectAsset, ProjectTemplate
from .user import User
from enum import Enum


class UserRole(str, Enum):
    CONTENT_CREATOR = "content_creator"
    CG_ARTIST = "cg_artist"


class SubscriptionTier(str, Enum):
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"


class AssetType(str, Enum):
    CLOTHING = "clothing"
    SHOES = "shoes"
    FURNITURE = "furniture"
    JEWELRY = "jewelry"
    VEHICLE = "vehicle"
    OTHER = "other"


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    FINISHED = "finished"


# Import models to ensure they're loaded

__all__ = [
    'UserRole',
    'SubscriptionTier',
    'AssetType',
    'ProjectStatus',
    'User',
    'Project',
    'ProjectAsset',
    'ProjectTemplate',
    'Asset',
    'Favorite',
    'Template'
]
