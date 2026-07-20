"""
Fast-launch ledger tests: repository upsert semantics, and the orchestrator
wiring that (a) records a machine as known-fast when a launch completes
under the threshold, and (b) tries known-fast machines first on a
subsequent launch for the same GPU tier before falling back to the general
search.

Run:  venv/bin/python -m pytest tests/test_provisioning_fast_launch.py -v
"""

import os

import pytest

os.environ.setdefault("LOGTO_INTERNAL_SECRET", "test-secret-not-for-real-use")

from app.services.provisioning.config import PhaseBudget, ProvisioningConfig
from app.services.provisioning.orchestrator import Orchestrator
from app.services.provisioning.repository import ProvisioningRepository

from provisioning_fakes import FakeSSHClient, FakeVastAIClient

pytestmark = pytest.mark.usefixtures("provisioning_db")


@pytest.fixture(autouse=True)
def tight_timeouts():
    ProvisioningConfig.reset()
    config = ProvisioningConfig.get()
    config.VAST_POLL_INTERVAL_SECONDS = 0.02
    config.VAST_PROVISIONING = PhaseBudget(stuck_seconds=1, ceiling_seconds=2)
    config.VAST_LOADING = PhaseBudget(stuck_seconds=1, ceiling_seconds=2)
    config.VAST_RUNNING_PENDING_NET = PhaseBudget(stuck_seconds=1, ceiling_seconds=2)
    config.FAST_LAUNCH_THRESHOLD_SECONDS = 5  # generous enough for a fast in-process test to clear
    yield
    ProvisioningConfig.reset()


@pytest.fixture
def repo():
    return ProvisioningRepository()


def make_orchestrator(repo, vastai=None, ssh=None):
    return Orchestrator(vastai or FakeVastAIClient(), ssh or FakeSSHClient(), repo)


class TestRepositoryUpsert:
    async def test_first_record_creates_a_row(self, repo):
        await repo.record_fast_launch(machine_id=42, gpu_name="RTX 3090", seconds=90, vastai_instance_id=1001)
        ids = await repo.list_fast_machine_ids("RTX 3090")
        assert ids == [42]

    async def test_a_faster_launch_improves_best_seconds(self, repo):
        await repo.record_fast_launch(42, "RTX 3090", seconds=90, vastai_instance_id=1001)
        await repo.record_fast_launch(42, "RTX 3090", seconds=60, vastai_instance_id=1002)

        async with repo._session() as session:
            from app.services.provisioning.models import FastLaunchMachine
            record = await session.get(FastLaunchMachine, 42)
        assert record.best_launch_seconds == 60
        assert record.fast_launch_count == 2

    async def test_a_slower_launch_does_not_regress_best_seconds(self, repo):
        await repo.record_fast_launch(42, "RTX 3090", seconds=60, vastai_instance_id=1001)
        await repo.record_fast_launch(42, "RTX 3090", seconds=90, vastai_instance_id=1002)

        async with repo._session() as session:
            from app.services.provisioning.models import FastLaunchMachine
            record = await session.get(FastLaunchMachine, 42)
        assert record.best_launch_seconds == 60
        assert record.fast_launch_count == 2

    async def test_list_is_ordered_fastest_first_and_scoped_by_gpu(self, repo):
        await repo.record_fast_launch(1, "RTX 3090", seconds=100, vastai_instance_id=1)
        await repo.record_fast_launch(2, "RTX 3090", seconds=50, vastai_instance_id=2)
        await repo.record_fast_launch(3, "RTX 4090", seconds=10, vastai_instance_id=3)

        ids = await repo.list_fast_machine_ids("RTX 3090")
        assert ids == [2, 1]


class TestOrchestratorRecordsFastLaunches:
    async def test_fast_launch_is_recorded_with_the_right_machine_id(self, repo):
        vastai = FakeVastAIClient()
        vastai.set_available_offers(
            [{"id": 777, "gpu_name": "RTX 3090", "dph_total": 0.4, "machine_id": 555}]
        )
        vastai.set_instance(777, actual_status="running", ssh_host="1.2.3.4", ssh_port=2222)
        orch = make_orchestrator(repo, vastai=vastai)

        await orch.launch_new_instance("alice", "RTX 3090", None, None)

        ids = await repo.list_fast_machine_ids("RTX 3090")
        assert ids == [555]

    async def test_launch_over_threshold_is_not_recorded(self, repo):
        import asyncio

        vastai = FakeVastAIClient()
        vastai.set_available_offers(
            [{"id": 778, "gpu_name": "RTX 3090", "dph_total": 0.4, "machine_id": 556}]
        )
        vastai.set_instance(778, actual_status="running", ssh_host="1.2.3.4", ssh_port=2222)

        class SlowSSH(FakeSSHClient):
            async def get_connection(self, instance_id, host, port):
                await asyncio.sleep(0.05)
                return await super().get_connection(instance_id, host, port)

        # -1, not 0: elapsed is an int truncation of a sub-second duration, so
        # a threshold of 0 would still (wrongly) pass a near-instant fake launch.
        ProvisioningConfig.get().FAST_LAUNCH_THRESHOLD_SECONDS = -1
        orch = make_orchestrator(repo, vastai=vastai, ssh=SlowSSH())

        await orch.launch_new_instance("alice", "RTX 3090", None, None)

        assert await repo.list_fast_machine_ids("RTX 3090") == []


class TestKnownFastMachineTriedFirst:
    async def test_uses_the_known_fast_machines_offer_when_available(self, repo):
        await repo.record_fast_launch(machine_id=555, gpu_name="RTX 3090", seconds=45, vastai_instance_id=111)

        vastai = FakeVastAIClient()
        # The known-fast machine currently has an offer up...
        vastai.set_available_offers(
            [{"id": 999, "gpu_name": "RTX 3090", "dph_total": 0.9, "machine_id": 555}]
        )
        vastai.set_instance(999, actual_status="running", ssh_host="1.2.3.4", ssh_port=2222)
        orch = make_orchestrator(repo, vastai=vastai)

        assignment = await orch.launch_new_instance("bob", "RTX 3090", None, None)

        assert assignment.instance_id == 999
        record = await repo.get_instance(999)
        assert record.machine_id == 555

    async def test_falls_back_to_general_search_when_the_known_fast_machine_is_unavailable(self, repo):
        await repo.record_fast_launch(machine_id=555, gpu_name="RTX 3090", seconds=45, vastai_instance_id=111)

        vastai = FakeVastAIClient()  # no set_available_offers -> machine_ids search returns [], forces fallback
        orch = make_orchestrator(repo, vastai=vastai)

        assignment = await orch.launch_new_instance("bob", "RTX 3090", None, None)

        # Fell back to the fake's default single-offer path (id 999001).
        assert assignment.instance_id == 999001
