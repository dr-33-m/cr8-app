"""
Teardown worker tests — the guaranteed-destroy loop. Verifies it never trusts
a single destroy_instance() call, retries on non-confirmation, and eventually
reaches confirmed_destroyed / confirmed_absent.

Run:  venv/bin/python -m pytest tests/test_provisioning_teardown_worker.py -v
"""

import asyncio

import pytest

from app.services.provisioning.config import ProvisioningConfig
from app.services.provisioning.errors import TeardownReason
from app.services.provisioning.repository import ProvisioningRepository
from app.services.provisioning.state_machine import LifecycleState
from app.services.provisioning.teardown_worker import TeardownWorker

from provisioning_fakes import FakeVastAIClient

pytestmark = pytest.mark.usefixtures("provisioning_db")

VASTAI_ID = 555001


@pytest.fixture(autouse=True)
def fast_backoff():
    ProvisioningConfig.reset()
    config = ProvisioningConfig.get()
    config.TEARDOWN_BASE_DELAY_SECONDS = 0.01
    config.TEARDOWN_MAX_DELAY_SECONDS = 0.05
    yield
    ProvisioningConfig.reset()


@pytest.fixture
def repo():
    return ProvisioningRepository()


class TestConfirmedDestroyed:
    async def test_confirms_once_vastai_reports_terminal(self, repo):
        vastai = FakeVastAIClient()
        vastai.set_instance(VASTAI_ID, actual_status="running")
        await repo.create_instance(VASTAI_ID, "RTX 3090", 3, lifecycle_state=LifecycleState.FAILED)
        await repo.enqueue_teardown(VASTAI_ID, TeardownReason.PROVISION_TIMEOUT)

        # Takes 3 destroy calls before VastAI actually reports it gone —
        # the worker must not give up or falsely confirm on attempt 1.
        vastai.confirm_destroy_after(VASTAI_ID, 3)
        worker = TeardownWorker(vastai, repo)

        for _ in range(5):
            await worker.run_once()
            await asyncio.sleep(0.03)

        intent = await repo.get_open_teardown(VASTAI_ID)
        assert intent is None  # closed — confirmed
        record = await repo.get_instance(VASTAI_ID)
        assert record.lifecycle_state == LifecycleState.DESTROYED.value
        assert len(vastai.destroyed_ids) >= 3

    async def test_confirms_once_instance_fully_vanishes_from_vastai(self, repo):
        """Regression test for a real production incident: the instance was
        actually already gone (VastAI's GET returned 200 with {"instances":
        null}), but the teardown worker kept retrying forever, logging "not
        yet terminal (actual_status=None)" — a parsing bug in
        get_instance_info, not an actual delay. Reproduces the exact
        vanish-not-exited shape here."""
        vastai = FakeVastAIClient()
        vastai.set_instance(VASTAI_ID, actual_status="running")
        vastai.vanish_after(VASTAI_ID, 1)
        await repo.create_instance(VASTAI_ID, "RTX 3090", 3, lifecycle_state=LifecycleState.FAILED)
        await repo.enqueue_teardown(VASTAI_ID, TeardownReason.IDLE_EXPIRED)
        worker = TeardownWorker(vastai, repo)

        await worker.run_once()

        intent = await repo.get_open_teardown(VASTAI_ID)
        assert intent is None  # confirmed on the very first pass, not retried
        record = await repo.get_instance(VASTAI_ID)
        assert record.lifecycle_state == LifecycleState.DESTROYED.value

    async def test_does_not_confirm_on_the_first_pass_if_not_yet_terminal(self, repo):
        vastai = FakeVastAIClient()
        vastai.set_instance(VASTAI_ID, actual_status="running")
        vastai.confirm_destroy_after(VASTAI_ID, 5)
        await repo.create_instance(VASTAI_ID, "RTX 3090", 3, lifecycle_state=LifecycleState.FAILED)
        await repo.enqueue_teardown(VASTAI_ID, TeardownReason.PROVISION_TIMEOUT)
        worker = TeardownWorker(vastai, repo)

        await worker.run_once()

        intent = await repo.get_open_teardown(VASTAI_ID)
        assert intent is not None
        assert intent.status == "destroy_requested"
        assert intent.attempts == 1


class TestConfirmedAbsent:
    async def test_confirms_absent_when_vastai_has_no_record_at_all(self, repo):
        """This is the reconciler's 'tracked but absent from VastAI' case —
        the worker must confirm on the very first poll, not wait around."""
        vastai = FakeVastAIClient()  # no instance registered at all
        await repo.create_instance(VASTAI_ID, "RTX 3090", 3, lifecycle_state=LifecycleState.FAILED)
        await repo.enqueue_teardown(VASTAI_ID, TeardownReason.RECONCILIATION_ORPHAN_ABSENT)
        worker = TeardownWorker(vastai, repo)

        await worker.run_once()

        intent = await repo.get_open_teardown(VASTAI_ID)
        assert intent is None
        record = await repo.get_instance(VASTAI_ID)
        assert record.lifecycle_state == LifecycleState.DESTROYED.value


class TestStuckAlerting:
    async def test_stuck_intents_are_surfaced_not_silently_decayed(self, repo):
        vastai = FakeVastAIClient()
        vastai.set_instance(VASTAI_ID, actual_status="running")  # never confirms
        await repo.create_instance(VASTAI_ID, "RTX 3090", 3, lifecycle_state=LifecycleState.FAILED)
        await repo.enqueue_teardown(VASTAI_ID, TeardownReason.PROVISION_TIMEOUT)
        worker = TeardownWorker(vastai, repo)

        # Sleep must clear the capped max backoff (0.05s) every iteration, or
        # some passes find nothing due yet and attempts stalls below the
        # threshold we're asserting against.
        for _ in range(15):
            await worker.run_once()
            await asyncio.sleep(0.06)

        stuck = await repo.list_stuck_teardown_intents(min_attempts=10, min_age_seconds=999999)
        assert len(stuck) == 1
        assert stuck[0].vastai_instance_id == VASTAI_ID
