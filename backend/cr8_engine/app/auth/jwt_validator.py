"""
Logto JWT validator using JWKS (RS256).

Fetches public keys from Logto's OIDC discovery endpoint and validates
access tokens issued by the Logto instance.
"""

import os
import logging
from typing import Optional

import jwt
from jwt import PyJWKClient

logger = logging.getLogger(__name__)

_validator_instance: Optional["LogtoJWTValidator"] = None


class LogtoJWTValidator:
    """Validates Logto-issued RS256 JWTs using JWKS."""

    def __init__(self):
        self.issuer = os.environ["LOGTO_ENDPOINT"].rstrip("/") + "/oidc"
        self.audience = os.environ["LOGTO_API_RESOURCE"]
        jwks_uri = f"{self.issuer}/jwks"
        self._jwks_client = PyJWKClient(
            jwks_uri,
            cache_keys=True,
            headers={"User-Agent": "cr8-engine/1.0"},
        )
        logger.info(f"LogtoJWTValidator initialized (issuer={self.issuer}, audience={self.audience})")

    def validate(self, token: str) -> dict:
        """
        Validate a Logto access token.

        Args:
            token: The raw JWT string from the Authorization header or Socket.IO auth.

        Returns:
            Decoded claims dict (sub, scope, iat, exp, etc.)

        Raises:
            jwt.exceptions.PyJWTError: If the token is invalid, expired, or has wrong issuer/audience.
        """
        signing_key = self._jwks_client.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES384", "RS256"],
            issuer=self.issuer,
            audience=self.audience,
            options={"require": ["exp", "iss", "aud", "sub"]},
        )
        return claims


def get_jwt_validator() -> LogtoJWTValidator:
    """Get or create the singleton JWT validator."""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = LogtoJWTValidator()
    return _validator_instance
