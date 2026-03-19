"""
Invite token redemption endpoint.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_auth
from app.db.engine import get_db
from app.db.models import User, Invitation

logger = logging.getLogger(__name__)

router = APIRouter()


class RedeemInviteRequest(BaseModel):
    token: str = Field(..., min_length=1, max_length=64)


class RedeemInviteResponse(BaseModel):
    approved: bool = True
    already_approved: bool = False


@router.post("/invitations/redeem", response_model=RedeemInviteResponse)
async def redeem_invite(
    body: RedeemInviteRequest,
    claims: dict = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    """
    Redeem an invite token to unlock project launching.
    Single-use: each token can only be redeemed by one user.
    """
    logto_id = claims["sub"]

    # Look up the user
    result = await db.execute(
        select(User).where(User.logto_id == logto_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Call POST /users/sync first.",
        )

    # Already approved — no need to redeem
    if user.is_approved:
        return RedeemInviteResponse(approved=True, already_approved=True)

    # Look up the invitation
    result = await db.execute(
        select(Invitation).where(Invitation.token == body.token.strip())
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid invite token.",
        )

    # Check expiry
    now = datetime.now(timezone.utc)
    if invitation.expires_at.tzinfo is None:
        expires_at = invitation.expires_at.replace(tzinfo=timezone.utc)
    else:
        expires_at = invitation.expires_at

    if now > expires_at:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Invite token has expired.",
        )

    # Check if already redeemed
    if invitation.redeemed_by is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Invite token has already been used.",
        )

    # Redeem: update invitation and approve user atomically
    invitation.redeemed_by = user.id
    invitation.redeemed_at = now
    user.is_approved = True
    user.updated_at = now

    await db.commit()

    logger.info(f"User {logto_id} redeemed invite token (invitation_id={invitation.id})")

    return RedeemInviteResponse(approved=True, already_approved=False)
