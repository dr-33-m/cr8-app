"""
Authentication module for cr8_engine.

Provides JWT validation for browser clients (Logto OIDC tokens)
and internal HMAC token validation for Blender service clients.
"""

from .jwt_validator import LogtoJWTValidator, get_jwt_validator
from .internal_token import generate_blender_token, validate_internal_token
from .dependencies import require_auth

__all__ = [
    "LogtoJWTValidator",
    "get_jwt_validator",
    "generate_blender_token",
    "validate_internal_token",
    "require_auth",
]
