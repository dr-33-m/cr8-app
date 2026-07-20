"""
Repository tests against a real Postgres (see conftest.py for how to point
one at TEST_DATABASE_URL). Focus: the durability invariants the whole
re-architecture depends on — idempotent teardown enqueue, illegal-transition
rejection, one-active-session-per-user.

Run:  venv/bin/python -m pytest tests/test_provisioning_repository.py -v
"""

import pytest

from app.services.provisioning.errors import TeardownReason
from app.services.provisioning.repository import ProvisioningRepository
from app.services.provisioning.state_machine import LifecycleState, IllegalTransitionError

pytestmark = pytest.mark.usefixtures("provisioning_db")

VASTAI_ID = 123456


@pytest.fixture
def repo():
    return ProvisioningRepository()


class TestInstanceLifecycle:
    async def test_create_and_get_round_trip(self, repo):
        record = await repo.create_instance(VASTAI_ID, "RTX 3090", 3)
        assert record.vastai_instance_id == VASTAI_ID
        assert record.lifecycle_state == LifecycleState.REQUESTED.value

        fetched = await repo.get_instance(VASTAI_ID)
        assert fetched is not None
        assert fetched.gpu_name == "RTX 3090"

    async def test_transition_happy_path(self, repo):
        await repo.create_instance(VASTAI_ID, "RTX 3090", 3, lifecycle_state=LifecycleState.OFFER_ACCEPTED)
        updated = await repo.transition(VASTAI_ID, LifecycleState.VAST_PROVISIONING)
        assert updated.lifecycle_state == LifecycleState.VAST_PROVISIONING.value

    async def test_illegal_transition_is_rejected_and_not_persisted(self, repo):
        await repo.create_instance(VASTAI_ID, "RTX 3090", 3, lifecycle_state=LifecycleState.REQUESTED)
        with pytest.raises(IllegalTransitionError):
            await repo.transition(VASTAI_ID, LifecycleState.ACTIVE)
        # Must not have partially applied.
        fetched = await repo.get_instance(VASTAI_ID)
        assert fetched.lifecycle_state == LifecycleState.REQUESTED.value

    async def test_transition_to_destroyed_stamps_destroyed_at(self, repo):
        await repo.create_instance(VASTAI_ID, "RTX 3090", 3, lifecycle_state=LifecycleState.FAILED)
        await repo.transition(VASTAI_ID, LifecycleState.DESTROYING)
        updated = await repo.transition(VASTAI_ID, LifecycleState.DESTROYED)
        assert updated.destroyed_at is not None


class TestUpdateSignals:
    async def test_first_poll_always_counts_as_changed(self, repo):
        await repo.create_instance(VASTAI_ID, "RTX 3090", 3)
        record, changed = await repo.update_signals(VASTAI_ID, "created", "scheduling", "running", None)
        assert changed is True
        assert record.vastai_actual_status == "created"
        assert record.last_state_change_at is not None

    async def test_identical_signal_tuple_does_not_count_as_changed(self, repo):
        await repo.create_instance(VASTAI_ID, "RTX 3090", 3)
        await repo.update_signals(VASTAI_ID, "loading", "loading", "running", None)
        _record, changed = await repo.update_signals(VASTAI_ID, "loading", "loading", "running", None)
        assert changed is False

    async def test_intended_status_alone_changing_does_not_count(self, repo):
        """Only (actual_status, cur_state, next_state) drive stuck-detection —
        intended_status flipping alone (e.g. a stop was requested) shouldn't
        reset the clock on its own."""
        await repo.create_instance(VASTAI_ID, "RTX 3090", 3)
        await repo.update_signals(VASTAI_ID, "running", "running", "running", None)
        _record, changed = await repo.update_signals(VASTAI_ID, "running", "running", "stopped", None)
        assert changed is False


class TestTeardownLedgerIdempotency:
    async def test_enqueue_creates_a_row(self, repo):
        await repo.create_instance(VASTAI_ID, "RTX 3090", 3)
        created = await repo.enqueue_teardown(VASTAI_ID, TeardownReason.PROVISION_TIMEOUT)
        assert created is True
        intent = await repo.get_open_teardown(VASTAI_ID)
        assert intent is not None
        assert intent.reason == TeardownReason.PROVISION_TIMEOUT.value

    async def test_second_enqueue_while_open_is_a_no_op(self, repo):
        """This is THE property the whole guaranteed-destroy mechanism leans
        on: multiple independent code paths (timeout, cancellation,
        reconciliation) can all try to enqueue teardown for the same instance
        without racing to create duplicate ledger rows."""
        await repo.create_instance(VASTAI_ID, "RTX 3090", 3)
        first = await repo.enqueue_teardown(VASTAI_ID, TeardownReason.PROVISION_TIMEOUT)
        second = await repo.enqueue_teardown(VASTAI_ID, TeardownReason.USER_CANCELLED)
        assert first is True
        assert second is False
        intent = await repo.get_open_teardown(VASTAI_ID)
        # The original reason wins — the second call didn't overwrite it.
        assert intent.reason == TeardownReason.PROVISION_TIMEOUT.value

    async def test_enqueue_after_confirmed_creates_a_fresh_row(self, repo):
        """Once an intent is confirmed_destroyed/confirmed_absent, the
        partial unique index no longer blocks a new one — covers the (rare)
        case of an instance somehow needing teardown again."""
        await repo.create_instance(VASTAI_ID, "RTX 3090", 3)
        await repo.enqueue_teardown(VASTAI_ID, TeardownReason.PROVISION_TIMEOUT)
        intent = await repo.get_open_teardown(VASTAI_ID)
        await repo.mark_teardown_confirmed(intent.id, "confirmed_destroyed")

        created_again = await repo.enqueue_teardown(VASTAI_ID, TeardownReason.RECONCILIATION_TERMINAL)
        assert created_again is True

    async def test_list_due_respects_next_attempt_at(self, repo):
        from datetime import datetime, timedelta, timezone

        await repo.create_instance(VASTAI_ID, "RTX 3090", 3)
        await repo.enqueue_teardown(VASTAI_ID, TeardownReason.PROVISION_TIMEOUT)
        intent = await repo.get_open_teardown(VASTAI_ID)

        await repo.mark_teardown_retry(intent.id, datetime.now(timezone.utc) + timedelta(hours=1), "not ready yet")
        due = await repo.list_due_teardown_intents()
        assert intent.id not in {i.id for i in due}

    async def test_dedup_still_works_if_the_partial_unique_index_is_missing(self, repo):
        """Regression test for a real production incident: enqueue_teardown
        used to rely on `ON CONFLICT ... WHERE ... DO NOTHING` matching
        ux_open_teardown_per_instance by inference, and that failed with
        `InvalidColumnReferenceError: no unique or exclusion constraint
        matching the ON CONFLICT specification` in production despite passing
        in this same test suite — almost certainly SQLAlchemy/asyncpg version
        drift, since both are unpinned in requirements.txt. Reproduce the
        exact production condition (no matching index at all) and confirm
        check-then-insert dedup still works without depending on it."""
        from sqlalchemy import text

        import app.db.engine as db_engine

        engine = db_engine.get_engine()
        async with engine.begin() as conn:
            await conn.execute(text("DROP INDEX ux_open_teardown_per_instance"))

        try:
            await repo.create_instance(VASTAI_ID, "RTX 3090", 3)
            first = await repo.enqueue_teardown(VASTAI_ID, TeardownReason.PROVISION_TIMEOUT)
            second = await repo.enqueue_teardown(VASTAI_ID, TeardownReason.USER_CANCELLED)
            assert first is True
            assert second is False
            intent = await repo.get_open_teardown(VASTAI_ID)
            assert intent.reason == TeardownReason.PROVISION_TIMEOUT.value
        finally:
            async with engine.begin() as conn:
                await conn.execute(
                    text(
                        "CREATE UNIQUE INDEX ux_open_teardown_per_instance ON teardown_intents (vastai_instance_id) "
                        "WHERE status NOT IN ('confirmed_destroyed', 'confirmed_absent')"
                    )
                )


class TestUserSessions:
    async def test_one_active_session_per_user_enforced_defensively(self, repo):
        await repo.create_instance(VASTAI_ID, "RTX 3090", 3)
        await repo.start_session(VASTAI_ID, "alice", 111)
        # Starting a second session for the same user must close the first —
        # otherwise the DB's partial unique index would reject the insert.
        second = await repo.start_session(VASTAI_ID, "alice", 222)
        active = await repo.get_active_session("alice")
        assert active.id == second.id
        assert active.blender_pid == 222

    async def test_end_session_returns_instance_id(self, repo):
        await repo.create_instance(VASTAI_ID, "RTX 3090", 3)
        await repo.start_session(VASTAI_ID, "alice", 111)
        instance_id = await repo.end_session("alice")
        assert instance_id == VASTAI_ID
        assert await repo.get_active_session("alice") is None

    async def test_find_available_instance_respects_capacity(self, repo):
        await repo.create_instance(VASTAI_ID, "RTX 3090", 1, lifecycle_state=LifecycleState.IDLE)
        available = await repo.find_available_instance("RTX 3090", 1)
        assert available is not None

        await repo.start_session(VASTAI_ID, "alice", 111)
        await repo.transition(VASTAI_ID, LifecycleState.ACTIVE)
        full = await repo.find_available_instance("RTX 3090", 1)
        assert full is None
