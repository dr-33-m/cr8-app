"""
ProvisioningManager tests — proves the automatic internal retry loop
(_launch_with_retry, MAX_LAUNCH_RETRIES=2) itself checks for a reusable
instance before each attempt, not just that reuse is possible in principle
(that's covered at the orchestrator level in test_provisioning_orchestrator.py).
This is the fix for "Try Again always launches a whole new instance" applied
to the *automatic*, no-user-interaction retry path.

Run:  venv/bin/python -m pytest tests/test_provisioning_manager.py -v
"""

import os

import pytest

os.environ.setdefault("LOGTO_INTERNAL_SECRET", "test-secret-not-for-real-use")

from app.services.provisioning.config import PhaseBudget, ProvisioningConfig
from app.services.provisioning.errors import ProvisionError
from app.services.provisioning.manager import ProvisioningManager
from app.services.provisioning.orchestrator import Orchestrator
from app.services.provisioning.ssh_client import LaunchError
from app.services.provisioning.state_machine import LifecycleState

from provisioning_fakes import FakeSSHClient, FakeVastAIClient

pytestmark = pytest.mark.usefixtures("provisioning_db")

VASTAI_ID = 999001


@pytest.fixture(autouse=True)
def tight_timeouts():
    ProvisioningConfig.reset()
    config = ProvisioningConfig.get()
    config.VAST_POLL_INTERVAL_SECONDS = 0.02
    config.VAST_PROVISIONING = PhaseBudget(stuck_seconds=0.3, ceiling_seconds=1)
    config.VAST_LOADING = PhaseBudget(stuck_seconds=0.3, ceiling_seconds=1)
    config.VAST_RUNNING_PENDING_NET = PhaseBudget(stuck_seconds=0.3, ceiling_seconds=1)
    yield
    ProvisioningConfig.reset()


def make_manager_with_fakes(vastai: FakeVastAIClient, ssh: FakeSSHClient) -> ProvisioningManager:
    """ProvisioningManager builds its own real VastAIClient/SSHClient in
    __init__ (needs no live credentials — just constructs objects) — swap
    them for fakes and rebuild the orchestrator that captured references to
    the real ones."""
    manager = ProvisioningManager()
    manager.vastai = vastai
    manager.ssh = ssh
    manager.orchestrator = Orchestrator(vastai, ssh, manager.repo)
    return manager


class TestAutomaticRetryReusesFreedInstance:
    async def test_second_internal_attempt_reuses_instance_freed_by_the_first(self):
        """First attempt's Blender launch crashes (non-fatal) -> instance
        recovers to IDLE. The SAME provision_for_user() call's internal retry
        (no user interaction, no new browser_ready) must find and reuse that
        instance instead of launching (and paying for) a second one."""
        vastai = FakeVastAIClient()
        vastai.set_instance(VASTAI_ID, actual_status="running", ssh_host="1.2.3.4", ssh_port=2222)
        ssh = FakeSSHClient(launch_error=LaunchError("blender_crashed", "boom"))
        manager = make_manager_with_fakes(vastai, ssh)

        # The first launch_blender call crashes; the second (on the retry,
        # against the SAME instance) succeeds.
        call_count = {"n": 0}
        original_launch_blender = ssh.launch_blender

        async def flaky_launch_blender(*args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise LaunchError("blender_crashed", "boom")
            return 4242

        ssh.launch_blender = flaky_launch_blender

        assignment = await manager.provision_for_user("alice", tier="creator")

        assert assignment.instance_id == VASTAI_ID
        assert call_count["n"] == 2
        # Only ONE VastAI instance was ever ordered — the second attempt
        # reused it rather than accepting a fresh offer.
        assert len(vastai.instances) == 1
        assert (VASTAI_ID, "alice") in ssh.orphan_kills

    async def test_instance_incompatible_still_launches_a_genuinely_new_instance(self):
        """Sanity check the distinction still holds the other way: a
        hardware-fatal failure must NOT be "reused" — it should still result
        in teardown, same as before this change."""
        vastai = FakeVastAIClient()
        vastai.set_instance(VASTAI_ID, actual_status="running", ssh_host="1.2.3.4", ssh_port=2222)
        ssh = FakeSSHClient(launch_error=LaunchError("xorg_all_drivers_failed", "no display"))
        manager = make_manager_with_fakes(vastai, ssh)

        with pytest.raises(ProvisionError):
            await manager.provision_for_user("alice", tier="creator")

        record = await manager.repo.get_instance(VASTAI_ID)
        assert record.lifecycle_state in (LifecycleState.DESTROYING.value, LifecycleState.DESTROYED.value)
