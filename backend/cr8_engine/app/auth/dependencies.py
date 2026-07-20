"""
FastAPI authentication dependencies.
"""

import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_db
from app.db.models import User

from .jwt_validator import get_jwt_validator

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    FastAPI dependency that validates a Logto JWT from the Authorization header.

    Returns:
        Decoded JWT claims (sub, scope, email, etc.)

    Raises:
        HTTPException 401: If the token is missing, invalid, or expired.
    """
    validator = get_jwt_validator()
    try:
        return validator.validate(credentials.credentials)
    except Exception as e:
        logger.warning(f"JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    claims: dict = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Resolve the authenticated caller to their User row, rejecting unapproved users.

    Prefer this over require_auth wherever the endpoint needs the user's identity:
    it returns the internal UUID (the correct key for per-user storage) and enforces
    the invite gate, which require_auth alone does not.
    """
    result = await db.execute(select(User).where(User.logto_id == claims["sub"]))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Call POST /users/sync first.",
        )
    if not user.is_approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is pending approval",
        )
    return user
