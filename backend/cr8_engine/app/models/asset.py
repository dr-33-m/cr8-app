from typing import Optional, Dict, Any, List
from sqlmodel import SQLModel, Field, Relationship, Column, JSON
from .user import User


class Asset(SQLModel, table=True):
    """
    Represents an asset in the system.

    Attributes:
        id (Optional[int]): The unique identifier of the asset.
        name (str): The name of the asset.
        description (Optional[str]): A description of the asset.
        asset_type (Optional[str]): The type of the asset.
        minio_path (str): The path to the asset in MinIO storage.
        creator_id (int): The ID of the user who created the asset.
        creator (User): The user who created the asset.
        price (Optional[float]): The price of the asset.
        is_public (bool): Whether the asset is public.
        controls (Dict[str, Any]): Scalable controls for the asset.
        project_assets (List[ProjectAsset]): The projects that the asset is used in.
        favorites (List[Favorite]): The users who have favorited the asset.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    asset_type: Optional[str] = Field(default=None)
    minio_path: str  # Path to asset in MinIO storage

    creator_id: int = Field(foreign_key="user.id")
    creator: "User" = Relationship(back_populates="created_assets")

    price: Optional[float] = None
    is_public: bool = Field(default=False)

    # Scalable controls for assets
    controls: Dict[str, Any] = Field(sa_column=Column(JSON), default={})

    # Relationships
    project_assets: List["ProjectAsset"] = Relationship(back_populates="asset")
    favorites: List["Favorite"] = Relationship(
        back_populates="asset")  # Add this line


class Favorite(SQLModel, table=True):
    """
    Represents a user's favorite asset or template.

    Attributes:
        id (Optional[int]): The unique identifier of the favorite.
        user_id (int): The ID of the user who favorited the asset or template.
        user (User): The user who favorited the asset or template.
        asset_id (Optional[int]): The ID of the asset that was favorited.
        template_id (Optional[int]): The ID of the template that was favorited.
        asset (Optional[Asset]): The asset that was favorited.
        template (Optional[Template]): The template that was favorited.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    user: "User" = Relationship(back_populates="favorites")

    asset_id: Optional[int] = Field(foreign_key="asset.id", default=None)
    template_id: Optional[int] = Field(foreign_key="template.id", default=None)

    # Relationships to Asset and Template
    asset: Optional["Asset"] = Relationship(back_populates="favorites")
    template: Optional["Template"] = Relationship(back_populates="favorites")
