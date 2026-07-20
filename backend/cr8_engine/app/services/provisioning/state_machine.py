"""
Explicit lifecycle state machine for a provisioned VastAI instance.

Replaces the legacy `InstanceRecord.status: "provisioning"|"running"` binary
(and the never-set "destroying" aspiration) with a state keyed off VastAI's
*real* signals — all four fields together (actual_status + cur_state +
intended_status + next_state), not actual_status alone — plus the existing
CR8:STATUS SSH-phase protocol for the post-boot Blender launch.

This module is pure/deterministic (no I/O, no asyncio) so it can be unit
tested in isolation and used as the single source of truth for what
transitions are legal, both here and in the repository layer.
"""

from enum import Enum


class LifecycleState(str, Enum):
    REQUESTED = "REQUESTED"
    OFFER_ACCEPTED = "OFFER_ACCEPTED"
    VAST_PROVISIONING = "VAST_PROVISIONING"
    VAST_LOADING = "VAST_LOADING"
    VAST_RUNNING_PENDING_NET = "VAST_RUNNING_PENDING_NET"
    SSH_KEY_ATTACHING = "SSH_KEY_ATTACHING"
    SSH_CONNECTING = "SSH_CONNECTING"
    BLENDER_LAUNCHING = "BLENDER_LAUNCHING"
    IDLE = "IDLE"
    ACTIVE = "ACTIVE"
    RECYCLING = "RECYCLING"
    FAILED = "FAILED"
    DESTROYING = "DESTROYING"
    DESTROYED = "DESTROYED"


# Legal forward transitions. FAILED/DESTROYING/DESTROYED are reachable from
# any non-terminal state (enforced separately in `transition()`, not listed
# per-source here to avoid repeating the same three edges 13 times).
_HAPPY_PATH_EDGES: dict[LifecycleState, set[LifecycleState]] = {
    LifecycleState.REQUESTED: {LifecycleState.OFFER_ACCEPTED},
    # The very first poll after accepting an offer can legitimately already
    # observe any of these three — VastAI doesn't guarantee we catch it at
    # "created" first (a cached image can reach "running" before our first
    # get_instance_info call lands).
    LifecycleState.OFFER_ACCEPTED: {
        LifecycleState.VAST_PROVISIONING,
        LifecycleState.VAST_LOADING,
        LifecycleState.VAST_RUNNING_PENDING_NET,
    },
    LifecycleState.VAST_PROVISIONING: {LifecycleState.VAST_LOADING, LifecycleState.VAST_RUNNING_PENDING_NET},
    LifecycleState.VAST_LOADING: {LifecycleState.VAST_RUNNING_PENDING_NET},
    # IDLE is also reachable directly — used when the reconciler adopts an
    # already-running orphan instance and treats it as available for reuse
    # without literally re-running the attach/connect/launch handshake for a
    # launch attempt that never happened (there is no in-flight user to launch
    # Blender for on a freshly-adopted instance).
    LifecycleState.VAST_RUNNING_PENDING_NET: {LifecycleState.SSH_KEY_ATTACHING, LifecycleState.IDLE},
    # IDLE is also reachable from every step of the SSH/Blender handshake — a
    # failure here means the *software* side of the launch didn't work, not
    # that the underlying VastAI machine is broken (that's confirmed alive by
    # the time this state is reached). Recovering to IDLE instead of forcing
    # through FAILED->DESTROYING lets the next attempt reuse the same paid-for
    # instance instead of provisioning (and paying for) a brand new one — see
    # orchestrator.py's _fail_attempt.
    LifecycleState.SSH_KEY_ATTACHING: {LifecycleState.SSH_CONNECTING, LifecycleState.IDLE},
    LifecycleState.SSH_CONNECTING: {LifecycleState.BLENDER_LAUNCHING, LifecycleState.IDLE},
    LifecycleState.BLENDER_LAUNCHING: {LifecycleState.IDLE, LifecycleState.ACTIVE},
    LifecycleState.IDLE: {LifecycleState.ACTIVE, LifecycleState.RECYCLING},
    LifecycleState.ACTIVE: {LifecycleState.IDLE, LifecycleState.RECYCLING},
    # A recycle destroys and recreates the container, so VastAI genuinely
    # re-runs (a subset of) the provisioning pipeline — re-enters wherever the
    # observed signals land, not always at SSH_KEY_ATTACHING.
    LifecycleState.RECYCLING: {
        LifecycleState.VAST_PROVISIONING,
        LifecycleState.VAST_LOADING,
        LifecycleState.VAST_RUNNING_PENDING_NET,
        LifecycleState.SSH_KEY_ATTACHING,
    },
    LifecycleState.FAILED: {LifecycleState.DESTROYING},
    LifecycleState.DESTROYING: {LifecycleState.DESTROYED},
}

_TERMINAL_ESCAPE_TARGETS = {LifecycleState.FAILED, LifecycleState.DESTROYING, LifecycleState.DESTROYED}
_TERMINAL_STATES = {LifecycleState.DESTROYED}


class IllegalTransitionError(Exception):
    def __init__(self, current: LifecycleState, target: LifecycleState):
        self.current = current
        self.target = target
        super().__init__(f"Illegal transition: {current} -> {target}")


def is_legal_transition(current: LifecycleState, target: LifecycleState) -> bool:
    """FAILED/DESTROYING/DESTROYED are reachable from any non-terminal state;
    everything else must follow the happy-path edge table. A same-state
    "transition" is always legal (no-op) — e.g. a second user joining an
    already-ACTIVE shared instance, or a duplicate signal-driven call."""
    if current == target:
        return True
    if current in _TERMINAL_STATES:
        return False
    if target in _TERMINAL_ESCAPE_TARGETS:
        # Still must respect the DESTROYING->DESTROYED / FAILED->DESTROYING edges
        # rather than allowing e.g. DESTROYING -> FAILED.
        if current in (LifecycleState.FAILED, LifecycleState.DESTROYING):
            return target in _HAPPY_PATH_EDGES.get(current, set())
        return True
    return target in _HAPPY_PATH_EDGES.get(current, set())


def assert_legal_transition(current: LifecycleState, target: LifecycleState) -> None:
    if not is_legal_transition(current, target):
        raise IllegalTransitionError(current, target)


# --- VastAI signal classification ---
#
# Terminal actual_status values never recover (confirmed against VastAI's own
# CLI docs): exited, unknown, offline. A queued host eviction (next_state ==
# "stopped" while we're trying to bring the instance up) is treated the same
# way — it will not become running on its own.
_TERMINAL_ACTUAL_STATUSES = {"exited", "unknown", "offline"}


def is_terminal(actual_status: str | None, intended_status: str | None, next_state: str | None) -> bool:
    if actual_status in _TERMINAL_ACTUAL_STATUSES:
        return True
    if next_state == "stopped" and intended_status == "running":
        return True
    return False


def classify_actual_status(actual_status: str | None, cur_state: str | None) -> LifecycleState | None:
    """Best-effort mapping from a raw VastAI actual_status (+ optional cur_state)
    to our LifecycleState, for the pre-SSH portion of the pipeline only. Returns
    None when the signal doesn't map to a specific pre-SSH state (e.g. already
    running with SSH established — that transition is driven by the orchestrator
    itself, not by this classifier)."""
    if actual_status in (None, "", "created"):
        return LifecycleState.VAST_PROVISIONING
    if actual_status == "loading":
        return LifecycleState.VAST_LOADING
    if actual_status == "running":
        return LifecycleState.VAST_RUNNING_PENDING_NET
    return None
