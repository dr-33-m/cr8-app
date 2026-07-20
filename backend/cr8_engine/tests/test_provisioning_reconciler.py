"""
Reconciler tests — the continuous sweep that closes the legacy silent-drop
bugs. Focus: a tracked instance absent from VastAI's list gets a teardown
intent (never just deleted from state), and an untracked-but-still-legitimately-
booting VastAI instance gets adopted rather than impatiently destroyed.

Run:  venv/bin/python -m pytest tests/test_provisioning_reconciler.py -v
"""

import pytest

from app.services.config import DeploymentConfig
from app.services.provisioning.reconciler import Reconciler
from app.services.provisioning.repository import ProvisioningRepository
from app.services.provisioning.ssh_client import SSHClient
from app.services.provisioning.state_machine import LifecycleState

from provisioning_fakes import FakeVastAIClient

pytestmark = pytest.mark.usefixtures("provisioning_db")

VASTAI_ID = 777001


@pytest.fixture(autouse=True)
def template_hash(monkeypatch):
    monkeypatch.setenv("VASTAI_TEMPLATE_HASH_ID", "our-template-hash")
    DeploymentConfig.reset()
    yield
    DeploymentConfig.reset()


@pytest.fixture
def repo():
    return ProvisioningRepository()


class FakeSSHForReconciler:
    """Reconciler only calls is_blender_running for user-session liveness —
    everything else can no-op."""

    async def is_blender_running(self, instance_id, username, pid):
        return True


class TestNeverSilentlyDropTracking:
    async def test_tracked_instance_absent_from_vastai_enqueues_teardown(self, repo):
        vastai = FakeVastAIClient()  # instance not in VastAI's list at all
        await repo.create_instance(VASTAI_ID, "RTX 3090", 3, lifecycle_state=LifecycleState.IDLE)
        reconciler = Reconciler(vastai, FakeSSHForReconciler(), repo)

        await reconciler.run_once()

        intent = await repo.get_open_teardown(VASTAI_ID)
        assert intent is not None
        assert intent.reason == "reconciliation_orphan_absent"
        # Must still be tracked (not silently deleted) until the teardown
        # worker actually confirms it.
        record = await repo.get_instance(VASTAI_ID)
        assert record is not None

    async def test_terminal_status_enqueues_teardown(self, repo):
        vastai = FakeVastAIClient()
        vastai.set_instance(VASTAI_ID, actual_status="exited")
        await repo.create_instance(VASTAI_ID, "RTX 3090", 3, lifecycle_state=LifecycleState.ACTIVE)
        reconciler = Reconciler(vastai, FakeSSHForReconciler(), repo)

        await reconciler.run_once()

        intent = await repo.get_open_teardown(VASTAI_ID)
        assert intent is not None
        assert intent.reason == "reconciliation_terminal"


class TestOrphanAdoption:
    async def test_adopts_still_loading_instance_instead_of_destroying_it(self, repo):
        """The legacy bug: 'not worth waiting for' impatience destroyed
        instances that were still legitimately pulling an image."""
        vastai = FakeVastAIClient()
        vastai.set_instance(
            VASTAI_ID, actual_status="loading", template_hash_id="our-template-hash", gpu_name="RTX 3090"
        )
        reconciler = Reconciler(vastai, FakeSSHForReconciler(), repo)

        await reconciler.run_once()

        record = await repo.get_instance(VASTAI_ID)
        assert record is not None
        assert record.lifecycle_state == LifecycleState.VAST_LOADING.value
        assert VASTAI_ID not in vastai.destroyed_ids

    async def test_adopts_running_instance_into_idle(self, repo):
        vastai = FakeVastAIClient()
        vastai.set_instance(
            VASTAI_ID, actual_status="running", ssh_host="1.2.3.4", ssh_port=2222,
            template_hash_id="our-template-hash", gpu_name="RTX 3090",
        )
        reconciler = Reconciler(vastai, FakeSSHForReconciler(), repo)

        await reconciler.run_once()

        record = await repo.get_instance(VASTAI_ID)
        assert record.lifecycle_state == LifecycleState.IDLE.value
        assert record.host == "1.2.3.4"
        assert VASTAI_ID in vastai.attach_calls

    async def test_never_adopts_or_touches_instances_outside_our_template(self, repo):
        vastai = FakeVastAIClient()
        vastai.set_instance(VASTAI_ID, actual_status="running", template_hash_id="someone-elses-template")
        reconciler = Reconciler(vastai, FakeSSHForReconciler(), repo)

        await reconciler.run_once()

        assert await repo.get_instance(VASTAI_ID) is None
        assert VASTAI_ID not in vastai.destroyed_ids

    async def test_already_terminal_orphan_is_destroyed_not_adopted(self, repo):
        vastai = FakeVastAIClient()
        vastai.set_instance(VASTAI_ID, actual_status="exited", template_hash_id="our-template-hash")
        reconciler = Reconciler(vastai, FakeSSHForReconciler(), repo)

        await reconciler.run_once()

        intent = await repo.get_open_teardown(VASTAI_ID)
        assert intent is not None
        assert intent.reason == "reconciliation_terminal"


class TestIdleExpiry:
    async def test_idle_past_timeout_enqueues_teardown(self, repo, monkeypatch):
        from app.services.provisioning.config import ProvisioningConfig

        ProvisioningConfig.reset()
        ProvisioningConfig.get().INSTANCE_IDLE_TIMEOUT = 0  # anything idle at all is "expired"

        vastai = FakeVastAIClient()
        vastai.set_instance(VASTAI_ID, actual_status="running")
        await repo.create_instance(VASTAI_ID, "RTX 3090", 3, lifecycle_state=LifecycleState.ACTIVE)
        await repo.start_session(VASTAI_ID, "alice", 111)
        await repo.end_session("alice")
        await repo.transition(VASTAI_ID, LifecycleState.IDLE)

        reconciler = Reconciler(vastai, FakeSSHForReconciler(), repo)
        await reconciler.run_once()

        intent = await repo.get_open_teardown(VASTAI_ID)
        assert intent is not None
        assert intent.reason == "idle_expired"
        ProvisioningConfig.reset()
