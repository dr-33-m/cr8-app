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

        # Which provisioning engine handles VastAI instance lifecycle:
        # "legacy" = app/services/instance_manager (flat JSON state, startup-only
        #   reconciliation) — current default, unchanged behavior.
        # "v2" = app/services/provisioning (Postgres-backed, continuous
        #   reconciliation, guaranteed-destroy ledger) — the re-architecture.
        # Defaults to legacy until v2 has been shadow-validated in production;
        # see the plan's rollout section before flipping this.
        self.PROVISIONING_ENGINE: str = os.getenv("PROVISIONING_ENGINE", "legacy")

        # Database (required for remote mode)
        self.DATABASE_URL: str = os.getenv("DATABASE_URL", "")

        # RustFS object storage (required for remote mode).
        # Two endpoints because presigned URLs sign the Host header — a URL signed
        # for one hostname fails against the other. PUBLIC is what the browser hits;
        # INTERNAL is what VastAI instances hit over the VPN. INTERNAL falls back to
        # PUBLIC so local dev works without a VPN.
        self.RUSTFS_PUBLIC_ENDPOINT: str = os.getenv("RUSTFS_PUBLIC_ENDPOINT", "")
        self.RUSTFS_INTERNAL_ENDPOINT: str = (
            os.getenv("RUSTFS_INTERNAL_ENDPOINT") or self.RUSTFS_PUBLIC_ENDPOINT
        )
        self.RUSTFS_ACCESS_KEY: str = os.getenv("RUSTFS_ACCESS_KEY", "")
        self.RUSTFS_SECRET_KEY: str = os.getenv("RUSTFS_SECRET_KEY", "")
        self.RUSTFS_BUCKET: str = os.getenv("RUSTFS_BUCKET", "cr8-xyz")

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
            logger.info(f"  PROVISIONING_ENGINE={self.PROVISIONING_ENGINE}")
            logger.info(f"  DATABASE_URL={'set' if self.DATABASE_URL else 'NOT SET'}")
            logger.info(f"  RUSTFS_PUBLIC_ENDPOINT={self.RUSTFS_PUBLIC_ENDPOINT or 'NOT SET'}")
            logger.info(f"  RUSTFS_INTERNAL_ENDPOINT={self.RUSTFS_INTERNAL_ENDPOINT or 'NOT SET'}")
            logger.info(f"  RUSTFS_ACCESS_KEY={'set' if self.RUSTFS_ACCESS_KEY else 'NOT SET'}")
            logger.info(f"  RUSTFS_BUCKET={self.RUSTFS_BUCKET}")
            # Normal user saves are multipart through the public endpoint, so
            # they work over the tunnel regardless. A distinct internal endpoint
            # (a RustFS address instances can reach directly) is still an optional
            # perf win: it bypasses the tunnel for downloads and the emergency
            # env-var save (a single PUT that would 413 past ~100MB otherwise).
            if not os.getenv("RUSTFS_INTERNAL_ENDPOINT"):
                logger.info(
                    "  RUSTFS_INTERNAL_ENDPOINT is unset — downloads and the "
                    "emergency save route via the public tunnel (fine, just not "
                    "the fastest path). Normal saves are multipart and unaffected.")

    def validate_remote_config(self) -> list[str]:
        """Validate that all required remote config is set. Returns list of errors."""
        errors = []
        if not self.VASTAI_API_KEY:
            errors.append("VASTAI_API_KEY is required for remote mode")
        if not self.VASTAI_TEMPLATE_HASH_ID:
            errors.append("VASTAI_TEMPLATE_HASH_ID is required for remote mode")
        if not self.DATABASE_URL:
            errors.append("DATABASE_URL is required for remote mode")
        if not self.RUSTFS_PUBLIC_ENDPOINT:
            errors.append("RUSTFS_PUBLIC_ENDPOINT is required for remote mode")
        if not self.RUSTFS_ACCESS_KEY:
            errors.append("RUSTFS_ACCESS_KEY is required for remote mode")
        if not self.RUSTFS_SECRET_KEY:
            errors.append("RUSTFS_SECRET_KEY is required for remote mode")
        return errors
