"""
User sync and profile endpoints.
"""

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_auth
from app.db.engine import get_db
from app.db.models import User

logger = logging.getLogger(__name__)

router = APIRouter()


class SyncUserRequest(BaseModel):
    email: str | None = None
    name: str | None = None
    picture: str | None = None


class UserResponse(BaseModel):
    id: str
    logto_id: str
    email: str | None
    name: str | None
    is_approved: bool
    created_at: datetime

    model_config = {"from_attributes": True}


@router.post("/users/sync", response_model=UserResponse)
async def sync_user(
    body: SyncUserRequest,
    claims: dict = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """
    Upsert the current user into the database.
    Called after login to ensure the user record exists.
    """
    logto_id = claims["sub"]

    stmt = pg_insert(User).values(
        id=uuid.uuid4(),
        logto_id=logto_id,
        email=body.email,
        name=body.name,
        picture=body.picture,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["logto_id"],
        set_={
            "email": stmt.excluded.email,
            "name": stmt.excluded.name,
            "picture": stmt.excluded.picture,
            "updated_at": datetime.now(timezone.utc),
        },
    )
    await db.execute(stmt)
    await db.commit()

    result = await db.execute(
        select(User).where(User.logto_id == logto_id)
    )
    user = result.scalar_one()

    return UserResponse(
        id=str(user.id),
        logto_id=user.logto_id,
        email=user.email,
        name=user.name,
        is_approved=user.is_approved,
        created_at=user.created_at,
    )


@router.get("/users/me", response_model=UserResponse)
async def get_me(
    claims: dict = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """Get the current user's profile."""
    logto_id = claims["sub"]

    result = await db.execute(
        select(User).where(User.logto_id == logto_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Call POST /users/sync first.",
        )

    return UserResponse(
        id=str(user.id),
        logto_id=user.logto_id,
        email=user.email,
        name=user.name,
        is_approved=user.is_approved,
        created_at=user.created_at,
    )
