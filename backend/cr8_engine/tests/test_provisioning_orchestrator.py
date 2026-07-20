"""
Orchestrator tests against a real Postgres + fake VastAI/SSH clients.

Focus: the guaranteed-teardown-on-any-failure property (the direct fix for
the legacy "last retry attempt never destroys" orphaning bug), stuck/ceiling
timeout enforcement using tight test budgets, and cancellation mid-attempt.

Run:  venv/bin/python -m pytest tests/test_provisioning_orchestrator.py -v
"""

import asyncio
import os

import pytest

os.environ.setdefault("LOGTO_INTERNAL_SECRET", "test-secret-not-for-real-use")

from app.services.provisioning.config import PhaseBudget, ProvisioningConfig
from app.services.provisioning.errors import ProvisionError, ProvisionReason, TeardownReason
from app.services.provisioning.orchestrator import Orchestrator
from app.services.provisioning.repository import ProvisioningRepository
from app.services.provisioning.ssh_client import LaunchError
from app.services.provisioning.state_machine import LifecycleState

from provisioning_fakes import FakeSSHClient, FakeVastAIClient

pytestmark = pytest.mark.usefixtures("provisioning_db")

VASTAI_ID = 999001  # matches FakeVastAIClient.search_offers's fixed offer id


@pytest.fixture(autouse=True)
def tight_timeouts():
    """Tiny stuck/ceiling budgets and poll interval so timeout tests run in
    milliseconds instead of minutes."""
    ProvisioningConfig.reset()
    config = ProvisioningConfig.get()
    config.VAST_POLL_INTERVAL_SECONDS = 0.02
    config.VAST_PROVISIONING = PhaseBudget(stuck_seconds=0.05, ceiling_seconds=0.3)
    config.VAST_LOADING = PhaseBudget(stuck_seconds=0.05, ceiling_seconds=0.3)
    config.VAST_RUNNING_PENDING_NET = PhaseBudget(stuck_seconds=0.05, ceiling_seconds=0.3)
    yield
    ProvisioningConfig.reset()


@pytest.fixture
def repo():
    return ProvisioningRepository()


def make_orchestrator(repo, vastai=None, ssh=None):
    return Orchestrator(vastai or FakeVastAIClient(), ssh or FakeSSHClient(), repo)


class TestHappyPath:
    async def test_launch_new_instance_succeeds_and_reaches_active(self, repo):
        vastai = FakeVastAIClient()
        vastai.set_instance(VASTAI_ID, actual_status="running", ssh_host="1.2.3.4", ssh_port=2222)
        orch = make_orchestrator(repo, vastai=vastai)

        assignment = await orch.launch_new_instance("alice", "RTX 3090", None, None)

        assert assignment.instance_id == VASTAI_ID
        assert assignment.host == "1.2.3.4"
        record = await repo.get_instance(VASTAI_ID)
        assert record.lifecycle_state == LifecycleState.ACTIVE.value
        session = await repo.get_active_session("alice")
        assert session is not None
        assert session.blender_pid == 4242
        assert await repo.get_open_teardown(VASTAI_ID) is None

    async def test_progresses_through_created_then_loading_then_running(self, repo):
        """Signal changes should reset the stuck clock — a slowly-progressing
        (but not actually stuck) instance must still succeed."""
        vastai = FakeVastAIClient()
        vastai.set_instance(VASTAI_ID, actual_status="created")
        orch = make_orchestrator(repo, vastai=vastai)

        async def progress():
            await asyncio.sleep(0.03)
            vastai.set_instance(VASTAI_ID, actual_status="loading")
            await asyncio.sleep(0.03)
            vastai.set_instance(VASTAI_ID, actual_status="running", ssh_host="1.2.3.4", ssh_port=2222)

        progress_task = asyncio.create_task(progress())
        assignment = await orch.launch_new_instance("alice", "RTX 3090", None, None)
        await progress_task
        assert assignment.instance_id == VASTAI_ID


class TestGuaranteedTeardownOnFailure:
    async def test_stuck_in_created_enqueues_teardown_and_raises(self, repo):
        vastai = FakeVastAIClient()
        vastai.set_instance(VASTAI_ID, actual_status="created")
        orch = make_orchestrator(repo, vastai=vastai)

        with pytest.raises(ProvisionError) as exc_info:
            await orch.launch_new_instance("alice", "RTX 3090", None, None)

        assert exc_info.value.reason == ProvisionReason.TIMEOUT.value
        intent = await repo.get_open_teardown(VASTAI_ID)
        assert intent is not None
        record = await repo.get_instance(VASTAI_ID)
        assert record.lifecycle_state == LifecycleState.DESTROYING.value

    async def test_terminal_status_during_wait_enqueues_teardown_immediately(self, repo):
        """exited/unknown/offline never recover — must not wait out the full
        stuck/ceiling budget before giving up."""
        vastai = FakeVastAIClient()
        vastai.set_instance(VASTAI_ID, actual_status="exited")
        orch = make_orchestrator(repo, vastai=vastai)

        with pytest.raises(ProvisionError):
            await orch.launch_new_instance("alice", "RTX 3090", None, None)

        assert await repo.get_open_teardown(VASTAI_ID) is not None

    async def test_xorg_failure_maps_to_instance_incompatible(self, repo):
        vastai = FakeVastAIClient()
        vastai.set_instance(VASTAI_ID, actual_status="running", ssh_host="1.2.3.4", ssh_port=2222)
        ssh = FakeSSHClient(launch_error=LaunchError("xorg_all_drivers_failed", "no display"))
        orch = make_orchestrator(repo, vastai=vastai, ssh=ssh)

        with pytest.raises(ProvisionError) as exc_info:
            await orch.launch_new_instance("alice", "RTX 3090", None, None)

        assert exc_info.value.reason == ProvisionReason.INSTANCE_INCOMPATIBLE.value
        assert await repo.get_open_teardown(VASTAI_ID) is not None


class TestNonFatalFailuresRecoverInsteadOfDestroy:
    """The "Try Again always launches a whole new instance, even though the
    one that just failed is still running" bug. A Blender-launch-phase
    failure with the machine confirmed alive should recover the instance to
    IDLE (killing any stray Blender process first) rather than destroying
    it — so the very next attempt (this loop's own retry, or a fresh
    provision_for_user() call from the user clicking Try Again) can reuse
    the same paid-for instance via connect_and_launch."""

    async def test_blender_crash_recovers_to_idle_not_destroyed(self, repo):
        vastai = FakeVastAIClient()
        vastai.set_instance(VASTAI_ID, actual_status="running", ssh_host="1.2.3.4", ssh_port=2222)
        ssh = FakeSSHClient(launch_error=LaunchError("blender_crashed", "boom"))
        orch = make_orchestrator(repo, vastai=vastai, ssh=ssh)

        with pytest.raises(ProvisionError) as exc_info:
            await orch.launch_new_instance("alice", "RTX 3090", None, None)

        assert exc_info.value.reason == ProvisionReason.BLENDER_CRASHED.value
        assert exc_info.value.instance_fatal is False
        assert await repo.get_open_teardown(VASTAI_ID) is None
        record = await repo.get_instance(VASTAI_ID)
        assert record.lifecycle_state == LifecycleState.IDLE.value
        assert (VASTAI_ID, "alice") in ssh.orphan_kills

    async def test_blender_launch_timeout_also_recovers_to_idle(self, repo):
        """Distinct from a VastAI-side wait timeout (still destroyed) — this
        is the SSH-connected-but-launch-blender.sh-hung case."""
        vastai = FakeVastAIClient()
        vastai.set_instance(VASTAI_ID, actual_status="running", ssh_host="1.2.3.4", ssh_port=2222)
        ssh = FakeSSHClient(launch_error=LaunchError("timeout", "launch-blender.sh hung"))
        orch = make_orchestrator(repo, vastai=vastai, ssh=ssh)

        with pytest.raises(ProvisionError):
            await orch.launch_new_instance("alice", "RTX 3090", None, None)

        assert await repo.get_open_teardown(VASTAI_ID) is None
        record = await repo.get_instance(VASTAI_ID)
        assert record.lifecycle_state == LifecycleState.IDLE.value

    async def test_recovered_instance_is_actually_reusable_via_find_available_instance(self, repo):
        """Prove the recovery is not just a state label — the standard reuse
        lookup (what provision_for_user calls on every new request, including
        the user's Try Again) must actually find it."""
        vastai = FakeVastAIClient()
        vastai.set_instance(VASTAI_ID, actual_status="running", ssh_host="1.2.3.4", ssh_port=2222)
        ssh = FakeSSHClient(launch_error=LaunchError("blender_crashed", "boom"))
        orch = make_orchestrator(repo, vastai=vastai, ssh=ssh)

        with pytest.raises(ProvisionError):
            await orch.launch_new_instance("alice", "RTX 3090", None, None)

        available = await repo.find_available_instance("RTX 3090", max_users=3)
        assert available is not None
        assert available.vastai_instance_id == VASTAI_ID

        # And a second attempt against that same record actually succeeds —
        # this is what "Try Again"/the automatic retry does next.
        ssh.launch_error = None  # simulate the transient issue having cleared
        assignment = await orch.connect_and_launch(available, "alice", None, None)
        assert assignment.instance_id == VASTAI_ID


class TestCancellation:
    async def test_cancel_mid_wait_enqueues_teardown_even_without_a_session(self, repo):
        vastai = FakeVastAIClient()
        vastai.set_instance(VASTAI_ID, actual_status="loading")  # never progresses on its own
        orch = make_orchestrator(repo, vastai=vastai)

        task = asyncio.create_task(orch.launch_new_instance("alice", "RTX 3090", None, None))
        # Let it get past offer-accept and into the polling loop, then cancel.
        await asyncio.sleep(0.06)
        task.cancel()

        with pytest.raises(asyncio.CancelledError):
            await task

        assert await repo.get_active_session("alice") is None
        intent = await repo.get_open_teardown(VASTAI_ID)
        assert intent is not None
        assert intent.reason == TeardownReason.USER_CANCELLED.value
        record = await repo.get_instance(VASTAI_ID)
        assert record.lifecycle_state == LifecycleState.DESTROYING.value
