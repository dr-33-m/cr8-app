"""
Deployment configuration for cr8_engine.
Loads settings from environment variables to support both local and remote (VastAI) launch modes.
"""

import os
import logging

logger = logging.getLogger(__name__)


# GPU tier mapping: tier name -> VastAI GPU name
TIER_GPU_MAP = {
    "creator": "RTX 3090",
    "pro": "RTX 4090",
    "studio": "RTX 5090",
}


class DeploymentConfig:
    """Centralized deployment configuration loaded from environment variables."""

    _instance = None

    def __init__(self):
        # Deployment mode
        self.LAUNCH_MODE: str = os.getenv("LAUNCH_MODE", "local")

        # VastAI settings
        self.VASTAI_API_KEY: str = os.getenv("VASTAI_API_KEY", "")
        self.VASTAI_TEMPLATE_HASH_ID: str = os.getenv("VASTAI_TEMPLATE_HASH_ID", "")

        # Instance limits
        self.MAX_USERS_PER_INSTANCE: int = int(os.getenv("MAX_USERS_PER_INSTANCE", "3"))
        self.INSTANCE_IDLE_TIMEOUT: int = int(os.getenv("INSTANCE_IDLE_TIMEOUT", "300"))

        # Database (required for remote mode)
        self.DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    @classmethod
    def get(cls) -> "DeploymentConfig":
        """Get singleton config instance."""
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._log_config()
        return cls._instance

    @classmethod
    def reset(cls):
        """Reset singleton (useful for testing)."""
        cls._instance = None

    def _log_config(self):
        logger.info(f"Deployment config loaded: LAUNCH_MODE={self.LAUNCH_MODE}")
        if self.LAUNCH_MODE == "remote":
            logger.info(f"  VASTAI_TEMPLATE_HASH_ID={self.VASTAI_TEMPLATE_HASH_ID or 'NOT SET'}")
            logger.info(f"  VASTAI_API_KEY={'set' if self.VASTAI_API_KEY else 'NOT SET'}")
            logger.info(f"  MAX_USERS_PER_INSTANCE={self.MAX_USERS_PER_INSTANCE}")
            logger.info(f"  INSTANCE_IDLE_TIMEOUT={self.INSTANCE_IDLE_TIMEOUT}s")
            logger.info(f"  DATABASE_URL={'set' if self.DATABASE_URL else 'NOT SET'}")

    def validate_remote_config(self) -> list[str]:
        """Validate that all required remote config is set. Returns list of errors."""
        errors = []
        if not self.VASTAI_API_KEY:
            errors.append("VASTAI_API_KEY is required for remote mode")
        if not self.VASTAI_TEMPLATE_HASH_ID:
            errors.append("VASTAI_TEMPLATE_HASH_ID is required for remote mode")
        if not self.DATABASE_URL:
            errors.append("DATABASE_URL is required for remote mode")
        return errors
