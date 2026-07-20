"""
Thin public facade over the new provisioning system — same method surface as
the legacy InstanceManager (provision_for_user/release_user/get_user_assignment/
initialize/shutdown) so blender_service.py and session_handlers.py don't need
to change beyond picking which manager class to instantiate.

The retry loop here is now trivial compared to the legacy _launch_and_assign:
orchestrator.launch_new_instance() already guarantees teardown of a failed
attempt's instance before it raises, so this loop only has to decide
retry-or-not — it never has to remember to destroy anything itself.
"""

import asyncio
import logging
from typing import Optional

from ..config import DeploymentConfig
from .attempts import get_registry
from .errors import ProvisionError, ProvisionReason, TeardownReason, RETRYABLE_REASONS
from .orchestrator import Orchestrator, InstanceAssignment
from .reconciler import Reconciler
from .repository import ProvisioningRepository
from .ssh_client import SSHClient
from .state_machine import LifecycleState
from .teardown_worker import TeardownWorker
from .vastai_client import VastAIClient

logger = logging.getLogger(__name__)

MAX_LAUNCH_RETRIES = 2


class ProvisioningManager:
    """v2 instance manager — Postgres-backed, continuous reconciliation,
    guaranteed teardown. See app/services/provisioning/ module docstrings for
    the design; see the plan for why this replaces app/services/instance_manager/."""

    def __init__(self):
        self.config = DeploymentConfig.get()
        self.vastai = VastAIClient()
        self.ssh = SSHClient()
        self.ssh.set_ssh_key(self.vastai.ssh_private_key)
        self.repo = ProvisioningRepository()
        self.orchestrator = Orchestrator(self.vastai, self.ssh, self.repo)
        self.teardown_worker = TeardownWorker(self.vastai, self.repo)
        self.reconciler = Reconciler(self.vastai, self.ssh, self.repo)
        self.attempts = get_registry()
        self._teardown_task: Optional[asyncio.Task] = None
        self._reconcile_task: Optional[asyncio.Task] = None
        logger.info("Provisioning manager (v2) initialized")

    async def initialize(self):
        """No startup-only reconciliation pass — the continuous reconciler
        (started here) supersedes it entirely, running the same logic forever
        instead of once at boot."""
        self._teardown_task = asyncio.create_task(self.teardown_worker.run_forever())
        self._reconcile_task = asyncio.create_task(self.reconciler.run_forever())
        logger.info("Teardown worker and reconciler started")

    async def periodic_maintenance(self):
        """No-op — kept only so main.py's engine-agnostic
        `create_task(manager.periodic_maintenance())` call works unchanged
        for both engines. v2's actual background work (teardown_worker,
        reconciler) is started in initialize() and stopped in shutdown()."""
        return

    async def provision_for_user(self, username: str, tier: str = "creator", status_callback=None,
                                 launch_env: dict = None) -> Optional[InstanceAssignment]:
        session = await self.repo.get_active_session(username)
        if session:
            instance = await self.repo.get_instance(session.vastai_instance_id)
            if instance and await self.ssh.is_blender_running(instance.vastai_instance_id, username, session.blender_pid):
                logger.info(f"User {username} already has running Blender on instance {instance.vastai_instance_id}")
                return InstanceAssignment(
                    instance_id=instance.vastai_instance_id, host=instance.host, ssh_port=instance.ssh_port,
                    gpu_name=instance.gpu_name, blender_pid=session.blender_pid,
                )
            await self.repo.end_session(username)

        gpu_name = self.vastai.get_gpu_for_tier(tier)
        if not gpu_name:
            raise ProvisionError(ProvisionReason.NO_GPU.value, f"Unknown tier: {tier}")

        record = await self.repo.find_available_instance(gpu_name, self.config.MAX_USERS_PER_INSTANCE)
        if record:
            logger.info(f"Reusing instance {record.vastai_instance_id}")
            try:
                self._register_attempt(username)
                return await self.orchestrator.connect_and_launch(record, username, launch_env, status_callback)
            except ProvisionError as e:
                sessions = await self.repo.list_active_sessions(record.vastai_instance_id)
                if e.reason == ProvisionReason.SSH_FAILED.value and not sessions:
                    logger.warning(f"SSH failed on reused instance {record.vastai_instance_id}, recycling")
                    return await self.orchestrator.recycle_and_reconnect(record, username, launch_env, status_callback)
                if e.reason == ProvisionReason.INSTANCE_INCOMPATIBLE.value:
                    logger.warning(f"Instance {record.vastai_instance_id} incompatible, destroying and launching new")
                    await self.repo.enqueue_teardown(record.vastai_instance_id, TeardownReason.HEALTH_CHECK_FAILED)
                    return await self._launch_with_retry(username, gpu_name, launch_env, status_callback)
                raise

        logger.info(f"No available {gpu_name} instance, launching new one for {username}")
        return await self._launch_with_retry(username, gpu_name, launch_env, status_callback)

    async def release_user(self, username: str) -> bool:
        session = await self.repo.get_active_session(username)
        if not session:
            logger.warning(f"No active session found for {username}")
            return False

        instance_id = session.vastai_instance_id
        await self.ssh.kill_blender(instance_id, username, session.blender_pid)
        await self.repo.end_session(username)

        remaining = await self.repo.list_active_sessions(instance_id)
        if not remaining:
            try:
                await self.repo.transition(instance_id, LifecycleState.IDLE)
            except Exception:
                logger.exception(f"Failed to transition instance {instance_id} to IDLE after last user left")

        logger.info(f"Released {username} from instance {instance_id} ({len(remaining)} users remaining)")
        return True

    async def get_user_assignment(self, username: str) -> Optional[InstanceAssignment]:
        session = await self.repo.get_active_session(username)
        if not session:
            return None
        instance = await self.repo.get_instance(session.vastai_instance_id)
        if not instance:
            return None
        return InstanceAssignment(
            instance_id=instance.vastai_instance_id, host=instance.host, ssh_port=instance.ssh_port,
            gpu_name=instance.gpu_name, blender_pid=session.blender_pid,
        )

    def cancel_launch(self, username: str) -> bool:
        """Cancels an in-flight provision_for_user() call for `username`, if
        any is registered. See attempts.py — this is a responsiveness
        fast-path; the reconciler is the actual teardown guarantee."""
        return self.attempts.cancel(username)

    async def shutdown(self):
        for task in (self._teardown_task, self._reconcile_task):
            if task:
                task.cancel()
        for task in (self._teardown_task, self._reconcile_task):
            if task:
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        await self.ssh.close_all()
        await self.vastai.close()
        logger.info("Provisioning manager (v2) shut down")

    # --- Private ---

    def _register_attempt(self, username: str) -> asyncio.Task:
        """Registers the *current* task as the in-flight attempt for username,
        so cancel_launch() can actually interrupt it. Must be called
        synchronously (no await) right at the start of a launch/connect
        attempt — the caller is assumed to already be running inside the task
        that was created for this request (session_handlers.py's
        on_browser_ready handler)."""
        task = asyncio.current_task()
        if task is not None:
            self.attempts.register(username, task)
        return task

    async def _launch_with_retry(self, username: str, gpu_name: str, launch_env: dict,
                                 status_callback) -> InstanceAssignment:
        """orchestrator.launch_new_instance() already guarantees teardown of an
        instance-fatal failure before raising — but a non-instance-fatal one
        (Blender/SSH software hiccup) instead recovers the instance to IDLE,
        so every retry attempt here checks find_available_instance() FIRST:
        if the previous attempt just freed one up, reuse it via
        connect_and_launch instead of paying for a brand new instance."""
        self._register_attempt(username)
        last_exc: Optional[ProvisionError] = None
        for attempt in range(MAX_LAUNCH_RETRIES):
            record = await self.repo.find_available_instance(gpu_name, self.config.MAX_USERS_PER_INSTANCE)
            try:
                if record:
                    logger.info(
                        f"Launch attempt {attempt + 1}/{MAX_LAUNCH_RETRIES} for {username}: "
                        f"reusing instance {record.vastai_instance_id} instead of launching fresh"
                    )
                    return await self.orchestrator.connect_and_launch(record, username, launch_env, status_callback)
                return await self.orchestrator.launch_new_instance(username, gpu_name, launch_env, status_callback)
            except ProvisionError as e:
                last_exc = e
                if record is not None:
                    # connect_and_launch never owns destroy/reuse decisions
                    # for a shared instance (by design), so it doesn't clean
                    # up after itself either — best-effort clear any
                    # half-started Blender process here so the next attempt
                    # (another retry, or a later Try Again) starts clean.
                    try:
                        await self.ssh.kill_orphaned_blender(record.vastai_instance_id, username)
                    except Exception:
                        logger.exception(f"Best-effort cleanup failed for {username} on instance {record.vastai_instance_id}")
                retryable = e.reason in RETRYABLE_REASONS
                if retryable and attempt < MAX_LAUNCH_RETRIES - 1:
                    logger.warning(
                        f"Launch attempt {attempt + 1}/{MAX_LAUNCH_RETRIES} failed ({e.reason}) for {username}, retrying"
                    )
                    if status_callback:
                        try:
                            await status_callback("retrying", 0)
                        except Exception:
                            pass
                    continue
                raise
        raise last_exc or ProvisionError(ProvisionReason.UNKNOWN.value, f"Failed after {MAX_LAUNCH_RETRIES} attempts")
