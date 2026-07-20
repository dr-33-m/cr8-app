"""
Closed error-reason taxonomy — the single source of truth for every string
that can reach the frontend as `InstanceStatusError.reason`.

Bug fixed (legacy bug #10): raw LaunchError.error_code strings and manager-level
reasons both used to reach the frontend inconsistently, with confirmed-missing
entries in the frontend's ERROR_REASONS map (instance_incompatible and several
raw codes). ProvisionError now normalizes any reason outside this closed set to
UNKNOWN rather than letting an unmapped string vanish into the UI's fallback —
the raw value is preserved on `.raw_reason` for logs/telemetry.

A test (tests/test_provisioning_error_taxonomy.py) asserts every value in
ALL_REASONS has a corresponding entry in the frontend's ERROR_REASONS map, so a
new reason added here without a matching UI message fails CI instead of
silently falling through to a generic message at runtime.
"""

from enum import Enum


class ProvisionReason(str, Enum):
    TIMEOUT = "timeout"
    SSH_FAILED = "ssh_failed"
    BLENDER_FAILED = "blender_failed"
    NO_GPU = "no_gpu"
    INSTANCE_INCOMPATIBLE = "instance_incompatible"
    LOCAL_FAILED = "local_failed"
    USER_CANCELLED = "user_cancelled"
    UNKNOWN = "unknown"

    # Raw launch-blender.sh CR8:ERROR codes surfaced directly (rather than
    # folded into BLENDER_FAILED) so the frontend can show a more specific
    # message than "Blender failed to start" — confirmed-missing from the
    # legacy frontend map, now closed.
    XORG_ALL_DRIVERS_FAILED = "xorg_all_drivers_failed"
    NVIDIA_DOWNLOAD_FAILED = "nvidia_download_failed"
    NVIDIA_EXTRACT_FAILED = "nvidia_extract_failed"
    NVIDIA_NOT_FOUND = "nvidia_not_found"
    NVIDIA_NO_VERSION = "nvidia_no_version"
    BLENDER_CRASHED = "blender_crashed"
    BLEND_DOWNLOAD_FAILED = "blend_download_failed"
    SSH_ERROR = "ssh_error"


ALL_REASONS: frozenset[str] = frozenset(r.value for r in ProvisionReason)

# error_code substrings that mean "this instance's GPU/driver setup is
# fundamentally broken, retrying on the same instance will never work" —
# same INSTANCE_FATAL_PATTERNS concept as the legacy manager.py, centralized.
INSTANCE_FATAL_PATTERNS: tuple[str, ...] = (
    "xorg", "nvidia_download", "nvidia_extract", "nvidia_not_found", "nvidia_no_version",
)

# ProvisionError.reason values treated as retryable (the manager's launch-retry
# loop will attempt again, up to MAX_LAUNCH_RETRIES) — everything else
# terminates the current provision_for_user() call immediately. NO_GPU/UNKNOWN/
# LOCAL_FAILED/USER_CANCELLED are excluded deliberately: retrying an
# instant-repeat "no offers right now" or an unclassified error blindly loops
# for no benefit, and a user's own cancellation should never be auto-retried.
RETRYABLE_REASONS: frozenset[str] = frozenset({
    ProvisionReason.TIMEOUT.value,
    ProvisionReason.INSTANCE_INCOMPATIBLE.value,
    ProvisionReason.SSH_FAILED.value,
    ProvisionReason.BLENDER_FAILED.value,
    ProvisionReason.BLENDER_CRASHED.value,
    ProvisionReason.BLEND_DOWNLOAD_FAILED.value,
    ProvisionReason.SSH_ERROR.value,
})


class ProvisionError(Exception):
    """Raised when provisioning fails with a specific, UI-facing reason.

    `instance_fatal` (default True — the conservative/safe default) tells the
    orchestrator whether the underlying VastAI machine itself is unusable
    (never came up, or a genuinely broken driver/hardware — must be
    destroyed) versus confirmed alive with only the Blender-launch software
    step failing (should be recovered to IDLE for reuse instead of destroyed
    — see orchestrator.py's `_fail_attempt`). Only call sites that have
    positively confirmed the VastAI machine is running should ever pass
    `instance_fatal=False`; getting this wrong in the "assume non-fatal"
    direction risks leaving a genuinely broken instance stuck in the reuse
    pool, so the default stays conservative."""

    def __init__(self, reason: str, message: str, instance_fatal: bool = True):
        self.raw_reason = reason
        self.reason = reason if reason in ALL_REASONS else ProvisionReason.UNKNOWN.value
        self.instance_fatal = instance_fatal
        super().__init__(message)


class TeardownReason(str, Enum):
    """Internal-only — why a teardown intent was enqueued. Never reaches the frontend."""
    PROVISION_TIMEOUT = "provision_timeout"
    LAST_RETRY_EXHAUSTED = "last_retry_exhausted"
    USER_CANCELLED = "user_cancelled"
    IDLE_EXPIRED = "idle_expired"
    RECONCILIATION_TERMINAL = "reconciliation_terminal"
    RECONCILIATION_ORPHAN_ABSENT = "reconciliation_orphan_absent"
    HEALTH_CHECK_FAILED = "health_check_failed"
    RECYCLE_FAILED = "recycle_failed"
    ADMIN_MANUAL = "admin_manual"
