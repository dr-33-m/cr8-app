"""
Pure unit tests for the provisioning lifecycle state machine — no I/O, no DB.

Run:  venv/bin/python -m pytest tests/test_provisioning_state_machine.py -v
"""

import pytest

from app.services.provisioning.state_machine import (
    LifecycleState,
    IllegalTransitionError,
    is_legal_transition,
    assert_legal_transition,
    is_terminal,
    classify_actual_status,
)


class TestHappyPath:
    def test_full_fresh_launch_sequence_is_legal(self):
        sequence = [
            LifecycleState.REQUESTED,
            LifecycleState.OFFER_ACCEPTED,
            LifecycleState.VAST_PROVISIONING,
            LifecycleState.VAST_LOADING,
            LifecycleState.VAST_RUNNING_PENDING_NET,
            LifecycleState.SSH_KEY_ATTACHING,
            LifecycleState.SSH_CONNECTING,
            LifecycleState.BLENDER_LAUNCHING,
            LifecycleState.ACTIVE,
        ]
        for a, b in zip(sequence, sequence[1:]):
            assert_legal_transition(a, b)  # must not raise

    def test_provisioning_can_skip_loading_straight_to_running(self):
        """A cold host can jump created -> running without a distinct 'loading'
        poll ever being observed (image already cached)."""
        assert_legal_transition(LifecycleState.VAST_PROVISIONING, LifecycleState.VAST_RUNNING_PENDING_NET)

    def test_active_idle_cycle(self):
        assert_legal_transition(LifecycleState.ACTIVE, LifecycleState.IDLE)
        assert_legal_transition(LifecycleState.IDLE, LifecycleState.ACTIVE)

    def test_recycle_reenters_provisioning_pipeline(self):
        for target in (
            LifecycleState.VAST_PROVISIONING,
            LifecycleState.VAST_LOADING,
            LifecycleState.VAST_RUNNING_PENDING_NET,
            LifecycleState.SSH_KEY_ATTACHING,
        ):
            assert_legal_transition(LifecycleState.RECYCLING, target)


class TestSameStateIsNoOp:
    @pytest.mark.parametrize("state", list(LifecycleState))
    def test_self_transition_always_legal(self, state):
        """Includes DESTROYED->DESTROYED: a repeated 'confirm destroyed' call
        (e.g. the teardown worker retrying after a crash mid-confirmation)
        must be idempotent, not an error."""
        assert is_legal_transition(state, state)


class TestFailureEscapeHatch:
    @pytest.mark.parametrize(
        "state",
        [
            LifecycleState.REQUESTED,
            LifecycleState.OFFER_ACCEPTED,
            LifecycleState.VAST_PROVISIONING,
            LifecycleState.VAST_LOADING,
            LifecycleState.VAST_RUNNING_PENDING_NET,
            LifecycleState.SSH_KEY_ATTACHING,
            LifecycleState.SSH_CONNECTING,
            LifecycleState.BLENDER_LAUNCHING,
            LifecycleState.IDLE,
            LifecycleState.ACTIVE,
            LifecycleState.RECYCLING,
        ],
    )
    def test_any_non_terminal_state_can_go_to_failed(self, state):
        assert_legal_transition(state, LifecycleState.FAILED)

    @pytest.mark.parametrize(
        "state",
        [
            LifecycleState.REQUESTED,
            LifecycleState.VAST_LOADING,
            LifecycleState.SSH_CONNECTING,
            LifecycleState.IDLE,
            LifecycleState.ACTIVE,
        ],
    )
    def test_any_non_terminal_state_can_go_straight_to_destroying(self, state):
        """The teardown ledger must be reachable from anywhere — this is the
        property the whole guaranteed-destroy mechanism depends on."""
        assert_legal_transition(state, LifecycleState.DESTROYING)

    def test_failed_must_go_through_destroying_not_directly_to_destroyed(self):
        assert not is_legal_transition(LifecycleState.FAILED, LifecycleState.DESTROYED)
        assert_legal_transition(LifecycleState.FAILED, LifecycleState.DESTROYING)
        assert_legal_transition(LifecycleState.DESTROYING, LifecycleState.DESTROYED)


class TestIllegalTransitions:
    def test_cannot_skip_from_requested_to_active(self):
        with pytest.raises(IllegalTransitionError):
            assert_legal_transition(LifecycleState.REQUESTED, LifecycleState.ACTIVE)

    def test_cannot_go_backwards_from_blender_launching_to_ssh_connecting(self):
        with pytest.raises(IllegalTransitionError):
            assert_legal_transition(LifecycleState.BLENDER_LAUNCHING, LifecycleState.SSH_CONNECTING)

    def test_destroyed_is_truly_terminal(self):
        for target in LifecycleState:
            if target == LifecycleState.DESTROYED:
                continue
            with pytest.raises(IllegalTransitionError):
                assert_legal_transition(LifecycleState.DESTROYED, target)

    def test_error_carries_current_and_target(self):
        try:
            assert_legal_transition(LifecycleState.REQUESTED, LifecycleState.ACTIVE)
            assert False, "should have raised"
        except IllegalTransitionError as e:
            assert e.current == LifecycleState.REQUESTED
            assert e.target == LifecycleState.ACTIVE


class TestIsTerminal:
    @pytest.mark.parametrize("status", ["exited", "unknown", "offline"])
    def test_documented_terminal_statuses(self, status):
        assert is_terminal(status, "running", None) is True

    @pytest.mark.parametrize("status", ["created", "loading", "running", None])
    def test_non_terminal_statuses(self, status):
        assert is_terminal(status, "running", None) is False

    def test_queued_eviction_is_terminal_even_if_actual_status_looks_fine(self):
        """next_state == 'stopped' while we're trying to bring it up means a
        host-initiated eviction is queued — it will not become running."""
        assert is_terminal("loading", "running", "stopped") is True

    def test_next_state_stopped_is_harmless_if_we_intended_to_stop(self):
        assert is_terminal("running", "stopped", "stopped") is False


class TestClassifyActualStatus:
    @pytest.mark.parametrize("status", [None, "", "created"])
    def test_maps_to_provisioning(self, status):
        assert classify_actual_status(status, None) == LifecycleState.VAST_PROVISIONING

    def test_loading_maps_to_vast_loading(self):
        assert classify_actual_status("loading", None) == LifecycleState.VAST_LOADING

    def test_running_maps_to_pending_net(self):
        assert classify_actual_status("running", None) == LifecycleState.VAST_RUNNING_PENDING_NET

    def test_unrecognized_status_maps_to_none(self):
        assert classify_actual_status("frozen", None) is None
