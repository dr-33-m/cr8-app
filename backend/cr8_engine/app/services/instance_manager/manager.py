"""
Instance Manager — orchestrates VastAI instances and SSH connections.
Handles provisioning, user assignment, health checks, and idle cleanup.
"""

import asyncio
import logging
import time
from typing import Optional

from ..config import DeploymentConfig
from ..vastai_service import VastAIService
from ..ssh_service import SSHService, LaunchError
from .models import UserSession, InstanceRecord, InstanceAssignment
from .state import InstanceManagerState

logger = logging.getLogger(__name__)


class ProvisionError(Exception):
    """Raised when instance provisioning fails with a specific reason."""

    def __init__(self, reason: str, message: str):
        self.reason = reason  # "timeout" | "ssh_failed" | "blender_failed" | "instance_incompatible" | "no_gpu"
        super().__init__(message)


class InstanceManager:
    """
    Coordinates VastAIService and SSHService to provision shared GPU instances
    and manage Blender process lifecycles.
    """

    def __init__(self):
        self.config = DeploymentConfig.get()
        self.vastai = VastAIService()
        self.ssh = SSHService()
        # Share the ephemeral SSH key from VastAI service with SSH service
        self.ssh.set_ssh_key(self.vastai.ssh_private_key)
        self.state = InstanceManagerState()
        self._maintenance_task: Optional[asyncio.Task] = None
        logger.info("Instance manager initialized")

    async def initialize(self):
        """Validate existing instances and adopt orphans from VastAI on startup."""
        logger.info("Initializing instance manager — validating existing state")
        stale_instances = []

        # Step 1: Validate instances in local state
        for instance_id, record in list(self.state.instances.items()):
            info = await self.vastai.get_instance_info(instance_id)
            if info is None or info.get("actual_status") not in ("running",):
                logger.warning(f"Instance {instance_id} is no longer running, removing from state")
                stale_instances.append(instance_id)
            else:
                # Instance is running — attach new SSH key (we have a fresh ephemeral key)
                await self.vastai.attach_ssh_key(instance_id)
                await asyncio.sleep(3)  # Brief propagation delay
                try:
                    await self.ssh.get_connection(instance_id, record.host, record.ssh_port)
                    for username, session in list(record.users.items()):
                        if not await self.ssh.is_blender_running(instance_id, username, session.blender_pid):
                            logger.warning(f"Blender for {username} (PID {session.blender_pid}) on {instance_id} is dead")
                            self.state.remove_user(username)
                except Exception as e:
                    logger.warning(f"Could not reconnect to instance {instance_id}: {e}")
                    stale_instances.append(instance_id)

        for instance_id in stale_instances:
            self.state.remove_instance(instance_id)

        # Step 2: Adopt orphan instances from VastAI that we don't have in state.
        # After engine restarts or crashes, running instances may still be on VastAI
        # but missing from our local state. Instead of destroying them (wasting the GPU),
        # adopt them so the next user gets an instant launch.
        tracked_ids = set(self.state.instances.keys())
        template_hash = self.config.VASTAI_TEMPLATE_HASH_ID
        try:
            vastai_instances = await self.vastai.list_instances()
            for inst in vastai_instances:
                inst_id = inst.get("id")
                inst_template = inst.get("template_hash_id")
                inst_status = inst.get("actual_status")

                if not inst_id or inst_template != template_hash or inst_id in tracked_ids:
                    continue

                if inst_status == "running":
                    ssh_host = inst.get("ssh_host") or inst.get("public_ipaddr")
                    ssh_port = inst.get("ssh_port") or inst.get("direct_port_start")
                    gpu_name = inst.get("gpu_name", "unknown")

                    if ssh_host and ssh_port:
                        logger.info(
                            f"Adopting orphan VastAI instance {inst_id} "
                            f"(gpu={gpu_name}, host={ssh_host}:{ssh_port})"
                        )
                        # Attach our new SSH key so we can connect
                        await self.vastai.attach_ssh_key(inst_id)
                        record = InstanceRecord(
                            vastai_id=inst_id,
                            gpu_name=gpu_name,
                            host=ssh_host,
                            ssh_port=int(ssh_port),
                            status="running",
                            max_users=self.config.MAX_USERS_PER_INSTANCE,
                            created_at=time.time(),
                            last_user_activity=time.time(),
                        )
                        self.state.add_instance(record)
                    else:
                        logger.warning(f"Orphan instance {inst_id} running but no SSH details, destroying")
                        await self.vastai.destroy_instance(inst_id)

                elif inst_status in ("loading", "created"):
                    # Still booting — not worth waiting for, destroy to avoid credit waste.
                    # If a user needs a GPU they'll launch a fresh one.
                    logger.info(f"Orphan instance {inst_id} still booting (status={inst_status}), destroying")
                    await self.vastai.destroy_instance(inst_id)

        except Exception as e:
            logger.warning(f"Failed to reconcile with VastAI (non-fatal): {e}")

        logger.info(f"Instance manager ready: {len(self.state.instances)} active instances")

    async def provision_for_user(self, username: str, tier: str = "creator", status_callback=None) -> Optional[InstanceAssignment]:
        """
        Provision a Blender instance for a user.
        Reuses an existing shared instance if available, otherwise launches a new one.
        """
        # Check for existing assignment
        existing_id = self.state.get_user_instance(username)
        if existing_id and existing_id in self.state.instances:
            record = self.state.instances[existing_id]
            session = record.users.get(username)
            if session and await self.ssh.is_blender_running(existing_id, username, session.blender_pid):
                logger.info(f"User {username} already has running Blender on instance {existing_id}")
                return InstanceAssignment(
                    instance_id=existing_id,
                    host=record.host,
                    ssh_port=record.ssh_port,
                    gpu_name=record.gpu_name,
                    blender_pid=session.blender_pid,
                )
            else:
                self.state.remove_user(username)

        # Resolve GPU from tier
        gpu_name = self.vastai.get_gpu_for_tier(tier)
        if not gpu_name:
            raise ProvisionError("no_gpu", f"Unknown tier: {tier}")

        # Try existing instance with capacity
        record = self.state.find_available_instance(gpu_name)
        if record:
            logger.info(f"Reusing instance {record.vastai_id} ({record.user_count}/{record.max_users} users)")
            try:
                return await self._assign_user_to_instance(username, record, status_callback=status_callback)
            except ProvisionError as e:
                if e.reason == "ssh_failed" and record.is_empty:
                    # SSH failed on a reused instance with no other users.
                    # The container likely has a stale authorized_keys (e.g. adopted orphan
                    # from a previous engine session). Recycle the container to get a fresh
                    # one with our current SSH key, then retry.
                    logger.warning(
                        f"SSH failed on reused instance {record.vastai_id}, "
                        f"recycling container to refresh SSH keys"
                    )
                    return await self._recycle_and_assign(username, record, status_callback)
                if e.reason == "instance_incompatible":
                    logger.warning(
                        f"Instance {record.vastai_id} incompatible ({e}), "
                        f"destroying and launching new instance"
                    )
                    await self._destroy_instance(record.vastai_id)
                    return await self._launch_and_assign(username, gpu_name, status_callback=status_callback)
                raise

        # Launch new instance
        logger.info(f"No available {gpu_name} instance, launching new one for {username}")
        return await self._launch_and_assign(username, gpu_name, status_callback=status_callback)

    async def release_user(self, username: str) -> bool:
        """Kill user's Blender process and remove their assignment."""
        instance_id = self.state.get_user_instance(username)
        if not instance_id or instance_id not in self.state.instances:
            logger.warning(f"No instance assignment found for {username}")
            return False

        record = self.state.instances[instance_id]
        session = record.users.get(username)

        if session:
            await self.ssh.kill_blender(instance_id, username, session.blender_pid)

        self.state.remove_user(username)
        logger.info(f"Released {username} from instance {instance_id} ({record.user_count} users remaining)")
        return True

    async def get_user_assignment(self, username: str) -> Optional[InstanceAssignment]:
        """Get the current instance assignment for a user."""
        instance_id = self.state.get_user_instance(username)
        if not instance_id or instance_id not in self.state.instances:
            return None

        record = self.state.instances[instance_id]
        session = record.users.get(username)
        if not session:
            return None

        return InstanceAssignment(
            instance_id=instance_id,
            host=record.host,
            ssh_port=record.ssh_port,
            gpu_name=record.gpu_name,
            blender_pid=session.blender_pid,
        )

    async def cleanup_idle_instances(self) -> int:
        """Destroy instances that have been empty longer than INSTANCE_IDLE_TIMEOUT."""
        destroyed = 0
        now = time.time()

        for instance_id, record in list(self.state.instances.items()):
            if record.is_empty and record.status == "running":
                idle_seconds = now - record.last_user_activity
                if idle_seconds >= self.config.INSTANCE_IDLE_TIMEOUT:
                    logger.info(f"Instance {instance_id} idle for {idle_seconds:.0f}s, destroying")
                    await self.ssh.close_connection(instance_id)
                    await self.vastai.destroy_instance(instance_id)
                    self.state.remove_instance(instance_id)
                    destroyed += 1

        if destroyed:
            logger.info(f"Cleaned up {destroyed} idle instances")
        return destroyed

    async def health_check(self):
        """Verify all tracked instances and Blender processes are alive."""
        for instance_id, record in list(self.state.instances.items()):
            if record.status != "running":
                continue

            info = await self.vastai.get_instance_info(instance_id)
            if info is None or info.get("actual_status") not in ("running",):
                logger.warning(f"Instance {instance_id} is no longer running on VastAI")
                self.state.remove_instance(instance_id)
                await self.ssh.close_connection(instance_id)
                continue

            for username, session in list(record.users.items()):
                if not await self.ssh.is_blender_running(instance_id, username, session.blender_pid):
                    logger.warning(f"Blender for {username} on instance {instance_id} has died")
                    self.state.remove_user(username)

    async def periodic_maintenance(self):
        """Background task — health checks and idle cleanup every 60s."""
        logger.info("Starting periodic maintenance task")
        while True:
            try:
                await asyncio.sleep(60)
                await self.health_check()
                await self.cleanup_idle_instances()
            except asyncio.CancelledError:
                logger.info("Periodic maintenance task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in periodic maintenance: {e}")

    async def shutdown(self):
        """Clean shutdown — cancel tasks, close SSH and HTTP connections."""
        if self._maintenance_task:
            self._maintenance_task.cancel()
        await self.ssh.close_all()
        await self.vastai.close()
        logger.info("Instance manager shut down")

    # --- Private ---

    async def _assign_user_to_instance(self, username: str, record: InstanceRecord,
                                       status_callback=None, launch_start: float = None) -> InstanceAssignment:
        """SSH into an existing instance and launch Blender for the user.

        Raises:
            ProvisionError: With reason "ssh_failed" or "blender_failed"
        """
        _start = launch_start or time.time()

        async def _emit(status: str):
            if status_callback:
                try:
                    await status_callback(status, int(time.time() - _start))
                except Exception:
                    pass

        # Step 1: Establish SSH connection
        await _emit("ssh_connecting")
        try:
            await self.ssh.get_connection(record.vastai_id, record.host, record.ssh_port)
        except Exception as e:
            logger.error(f"SSH connection failed for {username} on instance {record.vastai_id}: {e}")
            raise ProvisionError("ssh_failed", f"SSH connection failed to instance {record.vastai_id}: {e}")

        # Step 2: Launch Blender over SSH
        # Errors containing these patterns mean the instance's GPU/driver setup is
        # fundamentally broken and retrying on the same instance will never work.
        INSTANCE_FATAL_PATTERNS = ("xorg", "nvidia_download", "nvidia_extract", "nvidia_not_found", "nvidia_no_version")
        await _emit("blender_starting")

        # Adapter: bridge SSH service's single-arg callback to our (status, elapsed) signature
        ssh_cb = None
        if status_callback:
            async def ssh_cb(status: str):
                await status_callback(f"blender:{status}", int(time.time() - _start))

        try:
            pid = await self.ssh.launch_blender(record.vastai_id, username, status_callback=ssh_cb)
        except LaunchError as e:
            logger.error(f"Blender launch failed for {username} on instance {record.vastai_id}: {e}")
            if any(p in e.error_code for p in INSTANCE_FATAL_PATTERNS):
                raise ProvisionError("instance_incompatible", str(e))
            if e.error_code == "timeout":
                raise ProvisionError("timeout", str(e))
            raise ProvisionError("blender_failed", str(e))
        except Exception as e:
            logger.error(f"Blender launch exception for {username} on instance {record.vastai_id}: {e}")
            raise ProvisionError("blender_failed", f"Blender launch failed on instance {record.vastai_id}: {e}")

        session = UserSession(username=username, blender_pid=pid, started_at=time.time())
        self.state.add_user(record.vastai_id, session)

        return InstanceAssignment(
            instance_id=record.vastai_id,
            host=record.host,
            ssh_port=record.ssh_port,
            gpu_name=record.gpu_name,
            blender_pid=pid,
        )

    async def _launch_and_assign(self, username: str, gpu_name: str, status_callback=None) -> InstanceAssignment:
        """Launch a new VastAI instance and assign the user to it.
        Automatically retries with a fresh instance on timeout or incompatible hardware.

        Raises:
            ProvisionError: With reason "no_gpu", "ssh_failed", or "blender_failed"
        """
        MAX_RETRIES = 2
        launch_start = time.time()

        async def _emit(status: str):
            if status_callback:
                try:
                    await status_callback(status, int(time.time() - launch_start))
                except Exception:
                    pass

        for attempt in range(MAX_RETRIES):
            instance_id = await self.vastai.launch_instance(gpu_name=gpu_name)
            if instance_id is None:
                raise ProvisionError("no_gpu", f"No available GPU offers for {gpu_name}")

            record = InstanceRecord(
                vastai_id=instance_id,
                gpu_name=gpu_name,
                host="",
                ssh_port=0,
                status="provisioning",
                max_users=self.config.MAX_USERS_PER_INSTANCE,
                created_at=time.time(),
                last_user_activity=time.time(),
            )
            self.state.add_instance(record)

            try:
                connection_info = await self.vastai.wait_for_ready(instance_id, status_callback=status_callback)
                if connection_info is None:
                    raise ProvisionError("timeout", f"Instance {instance_id} did not become ready")

                record.host = connection_info["host"]
                record.ssh_port = connection_info["ssh_port"]
                record.status = "running"
                self.state.save()

                # Attach SSH key NOW that the container is running.
                # VastAI only writes the key into authorized_keys on a live container —
                # calling this before wait_for_ready returns 200 but has no effect.
                await _emit("ssh_key_attaching")
                logger.info(f"Attaching SSH key to running instance {instance_id}")
                key_attached = await self.vastai.attach_ssh_key(instance_id)
                if key_attached:
                    logger.info(f"SSH key attached, waiting 5s for authorized_keys propagation...")
                    await asyncio.sleep(5)
                else:
                    raise ProvisionError("ssh_failed", f"SSH key attachment failed for instance {instance_id}")

                return await self._assign_user_to_instance(
                    username, record, status_callback=status_callback, launch_start=launch_start
                )

            except ProvisionError as e:
                retryable = e.reason in ("timeout", "instance_incompatible", "ssh_failed")
                if retryable and attempt < MAX_RETRIES - 1:
                    logger.warning(
                        f"Instance {instance_id} failed ({e.reason}), "
                        f"attempt {attempt + 1}/{MAX_RETRIES}, retrying with a new instance"
                    )
                    await _emit("retrying")
                    await self._destroy_instance(instance_id)
                    continue
                raise

        # Should never reach here, but satisfy the type checker
        raise ProvisionError("blender_failed", f"Failed after {MAX_RETRIES} attempts")

    async def _destroy_instance(self, instance_id: int):
        """Tear down an instance fully — close SSH, destroy on VastAI, remove from state."""
        await self.ssh.close_connection(instance_id)
        await self.vastai.destroy_instance(instance_id)
        self.state.remove_instance(instance_id)

    async def _recycle_and_assign(self, username: str, record: InstanceRecord, status_callback=None) -> InstanceAssignment:
        """Recycle a running instance whose container has stale SSH keys, then assign the user.

        VastAI's recycle API destroys and recreates the container in place without
        losing the GPU slot. The fresh container will pick up our SSH key on startup.

        Raises:
            ProvisionError: With reason "ssh_failed", "timeout", or "blender_failed"
        """
        instance_id = record.vastai_id
        await self.ssh.close_connection(instance_id)

        recycled = await self.vastai.recycle_instance(instance_id)
        if not recycled:
            raise ProvisionError("ssh_failed", f"Failed to recycle instance {instance_id}")

        record.status = "provisioning"
        self.state.save()

        # Wait for the recycled container to come back up
        connection_info = await self.vastai.wait_for_ready(instance_id, status_callback=status_callback)
        if connection_info is None:
            # Instance is gone (destroyed externally or recycle failed).
            # Clean up our state and launch a fresh instance instead of giving up.
            logger.warning(f"Recycled instance {instance_id} did not come back, removing and launching fresh")
            await self._destroy_instance(instance_id)
            return await self._launch_and_assign(username, record.gpu_name, status_callback=status_callback)

        record.host = connection_info["host"]
        record.ssh_port = connection_info["ssh_port"]
        record.status = "running"
        self.state.save()

        # Attach SSH key to the fresh container
        logger.info(f"Attaching SSH key to recycled instance {instance_id}")
        key_attached = await self.vastai.attach_ssh_key(instance_id)
        if key_attached:
            logger.info(f"SSH key attached to recycled instance, waiting 15s for SSH proxy readiness...")
            await asyncio.sleep(15)
        else:
            raise ProvisionError("ssh_failed", f"SSH key attachment failed on recycled instance {instance_id}")

        return await self._assign_user_to_instance(username, record, status_callback=status_callback)
