"""
Continuous reconciliation loop — replaces the legacy system's three-way split
(startup-only initialize(), health_check(), cleanup_idle_instances(), each
with different blind spots gated on status=="running"). This runs forever,
diffing the FULL VastAI instance list against local state on every pass, not
just at process startup.

The one invariant that closes every legacy silent-drop bug: a local record is
never removed from tracking except via DESTROYED, which is only reachable
through a confirmed teardown intent (teardown_worker.py). A tracked instance
that's absent from VastAI's list is never just deleted from state — it gets a
teardown intent enqueued (the worker confirms `confirmed_absent` on first
poll). A VastAI instance we don't know about is adopted at its real inferred
state rather than destroyed out of impatience if it's still legitimately
booting.
"""

import asyncio
import logging
from datetime import datetime, timezone

from ..config import DeploymentConfig
from .config import ProvisioningConfig
from .errors import TeardownReason
from .models import ProvisionedInstance
from .repository import ProvisioningRepository
from .ssh_client import SSHClient
from .state_machine import LifecycleState, classify_actual_status, is_terminal
from .vastai_client import VastAIClient

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Reconciler:
    def __init__(self, vastai: VastAIClient, ssh: SSHClient, repo: ProvisioningRepository):
        self.vastai = vastai
        self.ssh = ssh
        self.repo = repo
        self.config = ProvisioningConfig.get()
        self.deployment_config = DeploymentConfig.get()

    async def run_forever(self):
        logger.info("Reconciler started")
        while True:
            try:
                await self.run_once()
            except asyncio.CancelledError:
                logger.info("Reconciler cancelled")
                raise
            except Exception:
                logger.exception("Reconciliation pass failed unexpectedly")
            await asyncio.sleep(self.config.RECONCILE_INTERVAL_SECONDS)

    async def run_once(self):
        vastai_list = await self.vastai.list_instances()
        vastai_by_id = {int(i["id"]): i for i in vastai_list if i.get("id") is not None}

        local = await self.repo.list_active_instances()
        local_ids = {r.vastai_instance_id for r in local}

        for record in local:
            # One instance's failure (e.g. a transient DB error) must not
            # abort reconciliation of every other instance this pass — that
            # would turn a single hiccup into a fleet-wide blackout instead
            # of a one-instance delay until the next pass.
            try:
                info = vastai_by_id.get(record.vastai_instance_id)
                if info is not None:
                    await self._reconcile_tracked(record, info)
                else:
                    # Never silently drop tracking — enqueue teardown; the
                    # worker confirms `confirmed_absent` on its first poll.
                    await self.repo.enqueue_teardown(
                        record.vastai_instance_id, TeardownReason.RECONCILIATION_ORPHAN_ABSENT
                    )
            except Exception:
                logger.exception(f"Failed to reconcile instance {record.vastai_instance_id} this pass, will retry next pass")

        template_hash = self.deployment_config.VASTAI_TEMPLATE_HASH_ID
        for inst_id, info in vastai_by_id.items():
            if inst_id in local_ids:
                continue
            # Never destroy anything we can't prove is ours.
            if info.get("template_hash_id") != template_hash:
                continue
            try:
                await self._adopt(inst_id, info)
            except Exception:
                logger.exception(f"Failed to adopt untracked instance {inst_id} this pass, will retry next pass")

    async def _reconcile_tracked(self, record: ProvisionedInstance, info: dict) -> None:
        vastai_id = record.vastai_instance_id
        actual_status = info.get("actual_status")
        cur_state = info.get("cur_state")
        intended_status = info.get("intended_status")
        next_state = info.get("next_state")

        updated, _changed = await self.repo.update_signals(vastai_id, actual_status, cur_state, intended_status, next_state)

        if is_terminal(actual_status, intended_status, next_state):
            await self.repo.enqueue_teardown(vastai_id, TeardownReason.RECONCILIATION_TERMINAL)
            return

        state = LifecycleState(updated.lifecycle_state)

        if state == LifecycleState.IDLE:
            idle_since = await self.repo.get_idle_since(vastai_id)
            if idle_since is not None:
                idle_seconds = (_utcnow() - idle_since).total_seconds()
                if idle_seconds >= self.config.INSTANCE_IDLE_TIMEOUT:
                    logger.info(f"Instance {vastai_id} idle for {idle_seconds:.0f}s, enqueueing teardown")
                    await self.repo.enqueue_teardown(vastai_id, TeardownReason.IDLE_EXPIRED)
                    return

        if state == LifecycleState.ACTIVE:
            await self._reconcile_user_sessions(record)

    async def _reconcile_user_sessions(self, record: ProvisionedInstance) -> None:
        """Detect Blender processes that died without the socket layer noticing
        (mirrors the legacy health_check's per-user liveness check)."""
        sessions = await self.repo.list_active_sessions(record.vastai_instance_id)
        any_alive = False
        for s in sessions:
            try:
                alive = await self.ssh.is_blender_running(record.vastai_instance_id, s.username, s.blender_pid)
            except Exception:
                # Connectivity trouble shouldn't be mistaken for "user's Blender died" —
                # skip this user this pass rather than ending a possibly-fine session.
                any_alive = True
                continue
            if alive:
                any_alive = True
            else:
                logger.warning(f"Blender for {s.username} on instance {record.vastai_instance_id} has died")
                await self.repo.end_session(s.username)

        if not any_alive and sessions:
            try:
                await self.repo.transition(record.vastai_instance_id, LifecycleState.IDLE)
            except Exception:
                logger.exception(f"Failed to transition instance {record.vastai_instance_id} to IDLE")

    async def _adopt(self, vastai_id: int, info: dict) -> None:
        actual_status = info.get("actual_status")
        cur_state = info.get("cur_state")
        intended_status = info.get("intended_status")
        next_state = info.get("next_state")
        gpu_name = info.get("gpu_name", "unknown")

        if is_terminal(actual_status, intended_status, next_state):
            # Already dead — nothing to adopt, just make sure it's actually gone.
            logger.info(f"Discovered untracked instance {vastai_id} already terminal ({actual_status}), destroying")
            await self.repo.create_instance(vastai_id, gpu_name, self.deployment_config.MAX_USERS_PER_INSTANCE, adopted=True)
            await self.repo.enqueue_teardown(vastai_id, TeardownReason.RECONCILIATION_TERMINAL)
            return

        inferred = classify_actual_status(actual_status, cur_state) or LifecycleState.VAST_PROVISIONING
        logger.info(f"Adopting untracked VastAI instance {vastai_id} (gpu={gpu_name}, inferred_state={inferred.value})")

        record = await self.repo.create_instance(
            vastai_id, gpu_name, self.deployment_config.MAX_USERS_PER_INSTANCE,
            lifecycle_state=LifecycleState.OFFER_ACCEPTED, adopted=True,
        )
        await self.repo.update_signals(vastai_id, actual_status, cur_state, intended_status, next_state)
        if inferred != LifecycleState.OFFER_ACCEPTED:
            await self.repo.transition(vastai_id, inferred)

        if inferred == LifecycleState.VAST_RUNNING_PENDING_NET:
            ssh_host = info.get("ssh_host") or info.get("public_ipaddr")
            ssh_port = info.get("ssh_port") or info.get("direct_port_start")
            if ssh_host and ssh_port:
                await self.repo.set_connection_info(vastai_id, ssh_host, int(ssh_port))
                await self.vastai.attach_ssh_key(vastai_id)
                # Land directly in IDLE (reusable, no known users) — there is no
                # in-flight launch attempt to run the normal attach/connect/launch
                # sequence for, so faking those steps would misrepresent the audit
                # trail. The next real assignment goes through connect_and_launch
                # normally from here.
                await self.repo.transition(vastai_id, LifecycleState.IDLE)
