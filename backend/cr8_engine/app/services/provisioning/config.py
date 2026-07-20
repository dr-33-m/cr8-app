"""
Provisioning-specific configuration: every timeout/retry/interval value that the
old system scattered as numeric literals across manager.py/vastai_service.py/
ssh_service.py lives here, centralized and env-overridable.

Each provisioning phase gets TWO independent budgets, not one flat timeout:
  - stuck seconds:   no observed change in the phase's real signal (VastAI's
                      actual_status/cur_state/next_state tuple, or a CR8:STATUS
                      line) for this long -> treat as hung.
  - ceiling seconds:  hard wall-clock cap on the phase regardless of activity,
                      a last-resort safety valve.

Numbers are ship-conservative defaults informed by the current code's existing
constants plus VastAI's own published data point (~15GB image = 5-10min pull).
They are meant to be retuned from real provisioning_events telemetry, not
guessed twice — see PhaseBudget docstring.
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class PhaseBudget:
    """Two independent timeout signals for one provisioning phase."""
    stuck_seconds: int
    ceiling_seconds: int


def _env_int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


class ProvisioningConfig:
    """Centralized, env-overridable provisioning timeout/retry policy."""

    _instance = None

    def __init__(self):
        # --- VastAI-side polling cadence ---
        self.VAST_POLL_INTERVAL_SECONDS: float = float(os.getenv("PROVISIONING_VAST_POLL_INTERVAL", "10"))

        # --- Reconciliation loop ---
        # No documented VastAI rate limit to tune against, so start conservative.
        self.RECONCILE_INTERVAL_SECONDS: int = _env_int("PROVISIONING_RECONCILE_INTERVAL", 30)

        # --- Teardown worker ---
        self.TEARDOWN_BASE_DELAY_SECONDS: float = float(os.getenv("PROVISIONING_TEARDOWN_BASE_DELAY", "5"))
        self.TEARDOWN_MAX_DELAY_SECONDS: float = float(os.getenv("PROVISIONING_TEARDOWN_MAX_DELAY", "300"))
        self.TEARDOWN_BACKOFF_FACTOR: float = 2.0
        self.TEARDOWN_STUCK_ATTEMPTS_ALERT: int = 10  # log CRITICAL past this many attempts
        self.TEARDOWN_STUCK_AGE_SECONDS: int = 1800    # or past this age

        # --- Whole-attempt backstop ---
        self.WHOLE_ATTEMPT_CEILING_SECONDS: int = _env_int("PROVISIONING_ATTEMPT_CEILING", 20 * 60)

        # --- Per-phase budgets (VastAI-side) ---
        self.OFFER_SEARCH_MAX_ATTEMPTS: int = 3
        self.OFFER_SEARCH_BASE_DELAY_SECONDS: float = 2.0
        self.OFFER_SEARCH_CEILING_SECONDS: int = 30

        self.VAST_PROVISIONING = PhaseBudget(
            stuck_seconds=_env_int("PROVISIONING_VAST_PROVISIONING_STUCK", 90),
            ceiling_seconds=_env_int("PROVISIONING_VAST_PROVISIONING_CEILING", 180),
        )
        # Image pull. VastAI's own docs: ~15GB image typically takes 5-10min.
        # Ceiling gives ~1.5-3x headroom for slow hosts without being open-ended.
        self.VAST_LOADING = PhaseBudget(
            stuck_seconds=_env_int("PROVISIONING_VAST_LOADING_STUCK", 240),
            ceiling_seconds=_env_int("PROVISIONING_VAST_LOADING_CEILING", 900),
        )
        self.VAST_RUNNING_PENDING_NET = PhaseBudget(
            stuck_seconds=_env_int("PROVISIONING_PENDING_NET_STUCK", 60),
            ceiling_seconds=_env_int("PROVISIONING_PENDING_NET_CEILING", 180),
        )

        # --- SSH ---
        self.SSH_KEY_PROPAGATION_POLL_SECONDS: float = 3.0
        self.SSH_KEY_PROPAGATION_CEILING_SECONDS: int = 60
        self.SSH_CONNECT_MAX_ATTEMPTS: int = 5
        self.SSH_CONNECT_BASE_DELAY_SECONDS: float = 3.0
        self.SSH_CONNECT_BACKOFF_FACTOR: float = 2.0
        self.SSH_CONNECT_TIMEOUT_SECONDS: int = 30

        # --- Blender launch (CR8:STATUS phases over SSH) ---
        # Substring-matched against the CR8:STATUS:<step> string, same convention
        # as the legacy ssh_service.py — now exhaustive against every phase
        # launch-blender.sh actually emits (confirmed by reading the script).
        self.BLENDER_PHASE_TIMEOUTS: dict[str, int] = {
            "env_setup": 30,
            "nvidia_driver": 30,
            "nvidia_toolkit": 30,
            "nvidia_cached": 30,
            "nvidia_downloading": 180,
            "nvidia_installed": 30,
            "xorg_setup": 60,
            "xorg_already_running": 15,
            "xorg_trying": 60,
            "xorg_nvidia_failed_trying_modesetting": 60,
            "xorg_ready": 15,
            "gst_preflight": 30,
            "gst_scanner": 15,
            "gst_webrtcsink": 15,
            "gst_missing_libs": 15,
            "gst_plugin_file": 15,
            "glx": 15,
            "blend_downloading": 600,  # user .blend can be ~1GB pulled through the tunnel
            "blend_downloaded": 15,
            "blender_launching": 60,
        }
        self.BLENDER_DEFAULT_PHASE_TIMEOUT: int = 30

        # --- Idle cleanup (existing knob, still honored) ---
        self.INSTANCE_IDLE_TIMEOUT: int = _env_int("INSTANCE_IDLE_TIMEOUT", 300)

        # --- Geo-restriction (latency) ---
        # Two-letter VastAI/ISO country codes only — confirmed against VastAI's
        # own API docs, which document geolocation as "two letter country code,
        # e.g. {"in": ["US", "CA"]}" — there is no "EU"/continent-level literal.
        # Default centers on Germany (matches a Hetzner Falkenstein engine/
        # signaller deployment) plus nearby low-latency EU. Empty list (set
        # PROVISIONING_ALLOWED_COUNTRIES="") disables the filter entirely.
        _countries_env = os.getenv("PROVISIONING_ALLOWED_COUNTRIES", "DE,NL,PL,AT,CH,BE,CZ,DK,LU,FR")
        self.ALLOWED_GEOLOCATIONS: list[str] = (
            [c.strip().upper() for c in _countries_env.split(",") if c.strip()] if _countries_env.strip() else []
        )

        # --- Fast-launch ledger ---
        # A launch (offer accepted -> Blender fully up) at or under this many
        # seconds gets its machine_id recorded as "known fast"; future offer
        # searches try known-fast machines for the same GPU tier before the
        # general (geo-filtered) search.
        self.FAST_LAUNCH_THRESHOLD_SECONDS: int = _env_int("PROVISIONING_FAST_LAUNCH_THRESHOLD", 120)
        self.FAST_MACHINE_CANDIDATES_LIMIT: int = _env_int("PROVISIONING_FAST_MACHINE_LIMIT", 10)

        # --- Scope guard: never destroy anything outside this template ---
        # (read from DeploymentConfig at call sites — not duplicated here)

    @classmethod
    def get(cls) -> "ProvisioningConfig":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls):
        """Reset singleton (useful for testing)."""
        cls._instance = None
