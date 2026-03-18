"""
FastAPI authentication dependencies.
"""

import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

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
