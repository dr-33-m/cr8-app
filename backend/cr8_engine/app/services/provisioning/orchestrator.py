"""
Single-launch-attempt orchestration — hand-rolled, not pydantic_graph (this is
a linear pipeline with retries, not a branching decision graph; see the plan's
Context section for the reasoning). Every step writes its state to Postgres
via the repository before doing the next bit of work, and `launch_new_instance`
guarantees that ANY failure after a VastAI instance id has been allocated
results in a teardown intent being enqueued before the exception propagates —
this is the direct fix for the legacy "last retry attempt never destroys"
orphaning bug. The caller (manager.py) never has to remember to clean up.
"""

import asyncio
import logging
import time
from dataclasses import dataclass

import httpx

from ..config import DeploymentConfig
from .config import ProvisioningConfig
from .errors import ProvisionError, ProvisionReason, TeardownReason, INSTANCE_FATAL_PATTERNS
from .models import ProvisionedInstance
from .repository import ProvisioningRepository
from .ssh_client import SSHClient, LaunchError
from .state_machine import LifecycleState, classify_actual_status, is_terminal
from .vastai_client import VastAIClient

logger = logging.getLogger(__name__)


@dataclass
class InstanceAssignment:
    instance_id: int
    host: str
    ssh_port: int
    gpu_name: str
    blender_pid: int


class Orchestrator:
    def __init__(self, vastai: VastAIClient, ssh: SSHClient, repo: ProvisioningRepository):
        self.vastai = vastai
        self.ssh = ssh
        self.repo = repo
        self.config = ProvisioningConfig.get()
        self.deployment_config = DeploymentConfig.get()

    # --- Public entry points ---

    async def launch_new_instance(
        self, username: str, gpu_name: str, launch_env: dict | None, status_callback
    ) -> InstanceAssignment:
        """Search offers, accept one, wait for it to become ready, connect, and
        launch Blender. Guarantees: any failure past the point of having a
        vastai_id enqueues a teardown intent before raising — no orphan possible
        even on the very first attempt, independent of any retry loop above."""
        start = time.time()

        async def emit(status: str):
            if status_callback:
                try:
                    await status_callback(status, int(time.time() - start))
                except Exception:
                    pass

        vastai_id, machine_id = await self._accept_an_offer(gpu_name)
        if vastai_id is None:
            raise ProvisionError(ProvisionReason.NO_GPU.value, f"No available GPU offers for {gpu_name}")

        await self.repo.create_instance(
            vastai_id, gpu_name, self.deployment_config.MAX_USERS_PER_INSTANCE,
            lifecycle_state=LifecycleState.OFFER_ACCEPTED, machine_id=machine_id,
        )

        try:
            connection_info = await self._wait_for_vast_ready(vastai_id, emit)
            await self.repo.set_connection_info(vastai_id, connection_info["host"], connection_info["ssh_port"])

            record = await self.repo.get_instance(vastai_id)
            assignment = await self._connect_and_launch(record, username, launch_env, status_callback, start=start)

            elapsed = int(time.time() - start)
            if machine_id is not None and elapsed <= self.config.FAST_LAUNCH_THRESHOLD_SECONDS:
                try:
                    await self.repo.record_fast_launch(machine_id, gpu_name, elapsed, vastai_id)
                except Exception:
                    logger.exception(f"Failed to record fast launch for machine {machine_id} (non-fatal)")
            return assignment

        except asyncio.CancelledError:
            # A user cancelling is a deliberate "stop" — always tear down
            # rather than leaving a possibly-half-configured instance sitting
            # in the reuse pool for some other user to stumble into.
            await self._fail_attempt(vastai_id, True, TeardownReason.USER_CANCELLED, "cancelled", "cancelled", username)
            raise
        except ProvisionError as e:
            reason = (
                TeardownReason.PROVISION_TIMEOUT
                if e.reason == ProvisionReason.TIMEOUT.value
                else TeardownReason.LAST_RETRY_EXHAUSTED
            )
            await self._fail_attempt(vastai_id, e.instance_fatal, reason, e.reason, str(e), username)
            raise
        except Exception as e:
            await self._fail_attempt(vastai_id, True, TeardownReason.LAST_RETRY_EXHAUSTED, "unknown", str(e), username)
            raise ProvisionError(ProvisionReason.UNKNOWN.value, str(e))

    async def connect_and_launch(
        self, record: ProvisionedInstance, username: str, launch_env: dict | None, status_callback
    ) -> InstanceAssignment:
        """Reuse an already-running shared instance for another user. Does NOT
        enqueue teardown on failure — the caller decides (recycle vs destroy vs
        just propagate and let the reconciler's continuous sweep catch it)."""
        return await self._connect_and_launch(record, username, launch_env, status_callback, start=time.time())

    async def recycle_and_reconnect(
        self, record: ProvisionedInstance, username: str, launch_env: dict | None, status_callback
    ) -> InstanceAssignment:
        """Recycle a container with stale SSH keys, then connect+launch. Recycle
        failing is a strong signal the instance is unrecoverable, so (unlike
        connect_and_launch) this path does enqueue a teardown intent on failure —
        the caller should fall back to launch_new_instance."""
        vastai_id = record.vastai_instance_id
        start = time.time()

        async def emit(status: str):
            if status_callback:
                try:
                    await status_callback(status, int(time.time() - start))
                except Exception:
                    pass

        await self.ssh.close_connection(vastai_id)

        try:
            recycled = await self.vastai.recycle_instance(vastai_id)
            if not recycled:
                raise ProvisionError(ProvisionReason.SSH_FAILED.value, f"Failed to recycle instance {vastai_id}")

            await self.repo.transition(vastai_id, LifecycleState.RECYCLING)
            connection_info = await self._wait_for_vast_ready(vastai_id, emit)
            await self.repo.set_connection_info(vastai_id, connection_info["host"], connection_info["ssh_port"])
            record = await self.repo.get_instance(vastai_id)
            return await self._connect_and_launch(record, username, launch_env, status_callback, start=start)

        except asyncio.CancelledError:
            await self._fail_attempt(vastai_id, True, TeardownReason.USER_CANCELLED, "cancelled", "cancelled", username)
            raise
        except ProvisionError as e:
            # Unlike launch_new_instance, always treat a recycle-path failure
            # as instance-fatal regardless of e.instance_fatal: recycling was
            # already the "this container had SSH problems" recovery path, so
            # a further failure here means persistent, not transient, trouble.
            await self._fail_attempt(vastai_id, True, TeardownReason.RECYCLE_FAILED, e.reason, str(e), username)
            raise
        except Exception as e:
            await self._fail_attempt(vastai_id, True, TeardownReason.RECYCLE_FAILED, "unknown", str(e), username)
            raise ProvisionError(ProvisionReason.UNKNOWN.value, str(e))

    # --- Internals ---

    async def _fail_attempt(
        self, vastai_id: int, instance_fatal: bool, reason: TeardownReason, error_reason: str, error_message: str,
        username: str | None = None,
    ):
        """Best-effort bookkeeping around a failed attempt. MUST NEVER raise —
        this runs inside an `except` block whose job is to propagate the
        *original* error to the caller (blender_service.py only catches
        ProvisionError; anything else this function threw would silently
        replace the real reason with a generic "blender_failed" and, worse,
        skip the teardown/recovery entirely).

        instance_fatal=True: the VastAI machine never came up, or is
        confirmed broken (bad driver/hardware) — destroy it via the teardown
        ledger, same guaranteed-teardown-before-raising contract as before.

        instance_fatal=False: the machine is confirmed alive; only the
        software side of getting Blender running failed. Destroying it here
        was the exact bug being fixed — "Try Again" (or the manager's own
        automatic retry) would always provision a brand new instance even
        though the one that just failed was still running fine. Instead:
        best-effort kill any stray Blender process for this user, then
        recover the instance to IDLE so the very next attempt (automatic
        retry inside manager.py, or a fresh provision_for_user() call from
        the user clicking Try Again) finds and reuses it via the existing
        find_available_instance() reuse path — no new plumbing needed there,
        just not destroying a perfectly good instance in the first place."""
        if instance_fatal:
            try:
                await self.repo.transition(vastai_id, LifecycleState.FAILED, error_reason=error_reason, error_message=error_message[:2000])
            except Exception:
                logger.exception(f"Failed to record FAILED transition for instance {vastai_id} (continuing to teardown anyway)")
            try:
                await self.repo.transition(vastai_id, LifecycleState.DESTROYING)
            except Exception:
                logger.exception(f"Failed to record DESTROYING transition for instance {vastai_id} (continuing to teardown anyway)")
            try:
                await self.repo.enqueue_teardown(vastai_id, reason)
            except Exception:
                logger.critical(
                    f"enqueue_teardown itself failed for instance {vastai_id} (reason={reason.value}) — "
                    f"this instance is NOT yet guaranteed to be torn down by this attempt; "
                    f"relying on the reconciler to retry",
                    exc_info=True,
                )
            return

        logger.warning(
            f"Blender launch failed for {username} on instance {vastai_id} (reason={error_reason}) but the "
            f"machine itself is healthy — recovering it to IDLE for reuse instead of destroying it"
        )
        if username:
            try:
                await self.ssh.kill_orphaned_blender(vastai_id, username)
            except Exception:
                logger.exception(f"Best-effort stray-Blender cleanup failed for {username} on instance {vastai_id}")
        try:
            await self.repo.transition(vastai_id, LifecycleState.IDLE, error_reason=error_reason, error_message=error_message[:2000])
        except Exception:
            logger.exception(
                f"Failed to recover instance {vastai_id} to IDLE after a non-fatal launch failure — "
                f"it may be stuck unreachable for reuse until the reconciler catches it"
            )

    async def _accept_an_offer(self, gpu_name: str) -> tuple[int | None, int | None]:
        """Returns (instance_id, machine_id). Tries known-fast machines for
        this GPU tier first (the fast-launch ledger) — if any of them
        currently have a rentable offer, that's who we rent; a machine being
        "known fast" doesn't mean it's available right now, so this always
        falls back to the general (geo-filtered) search when it isn't."""
        template_hash_id = self.deployment_config.VASTAI_TEMPLATE_HASH_ID

        fast_machine_ids = await self.repo.list_fast_machine_ids(gpu_name, limit=self.config.FAST_MACHINE_CANDIDATES_LIMIT)
        if fast_machine_ids:
            fast_offers = await self.vastai.search_offers(gpu_name, machine_ids=fast_machine_ids)
            if fast_offers:
                logger.info(f"Found {len(fast_offers)} offer(s) on known-fast machines for {gpu_name}, trying those first")
                result = await self._try_offers(fast_offers, template_hash_id)
                if result[0] is not None:
                    return result

        offers = await self.vastai.search_offers(gpu_name)
        if not offers:
            logger.error(f"No available offers for {gpu_name}")
            return None, None
        return await self._try_offers(offers, template_hash_id)

    async def _try_offers(self, offers: list[dict], template_hash_id: str) -> tuple[int | None, int | None]:
        image = self.deployment_config.VASTAI_BLENDER_IMAGE or None
        for offer in offers:
            try:
                instance_id = await self.vastai.accept_offer(
                    offer["id"], template_hash_id, disk_gb=40, image=image
                )
                if instance_id is not None:
                    return instance_id, offer.get("machine_id")
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    logger.warning("Rate limited by VastAI, backing off before next offer")
                    await asyncio.sleep(5)
                    continue
                if "invalid template hash" in e.response.text or "template not accessible" in e.response.text:
                    # Config error affects every offer — fail fast.
                    return None, None
        logger.error("All offers exhausted")
        return None, None

    async def _wait_for_vast_ready(self, vastai_id: int, emit) -> dict:
        """Poll VastAI until running+SSH-reachable, using all four signal fields
        and a stuck-vs-ceiling budget per phase — not a single flat timeout.
        Raises ProvisionError(TIMEOUT) on terminal status or budget breach."""
        poll_interval = self.config.VAST_POLL_INTERVAL_SECONDS
        monotonic_now = time.monotonic
        phase_entered_at = monotonic_now()
        last_change_at = monotonic_now()
        starting_record = await self.repo.get_instance(vastai_id)
        current_state = LifecycleState(starting_record.lifecycle_state) if starting_record else LifecycleState.OFFER_ACCEPTED

        while True:
            info = await self.vastai.get_instance_info(vastai_id)
            actual_status = info.get("actual_status") if info else None
            cur_state = info.get("cur_state") if info else None
            intended_status = info.get("intended_status") if info else None
            next_state = info.get("next_state") if info else None

            record, changed = await self.repo.update_signals(vastai_id, actual_status, cur_state, intended_status, next_state)
            now = monotonic_now()
            if changed:
                last_change_at = now

            if is_terminal(actual_status, intended_status, next_state):
                raise ProvisionError(
                    ProvisionReason.TIMEOUT.value,
                    f"Instance {vastai_id} reached terminal VastAI status "
                    f"(actual={actual_status}, next_state={next_state})",
                )

            target_state = classify_actual_status(actual_status, cur_state)
            if target_state is not None and target_state != current_state:
                await self.repo.transition(vastai_id, target_state)
                current_state = target_state
                phase_entered_at = now  # real phase change resets the ceiling clock

            if current_state == LifecycleState.VAST_RUNNING_PENDING_NET and info:
                ssh_host = info.get("ssh_host") or info.get("public_ipaddr")
                ssh_port = info.get("ssh_port") or info.get("direct_port_start")
                if ssh_host and ssh_port:
                    logger.info(f"Instance {vastai_id} ready: host={ssh_host}, ssh_port={ssh_port}")
                    return {"host": ssh_host, "ssh_port": int(ssh_port)}
                budget = self.config.VAST_RUNNING_PENDING_NET
            elif current_state == LifecycleState.VAST_LOADING:
                budget = self.config.VAST_LOADING
            else:
                budget = self.config.VAST_PROVISIONING

            stuck_elapsed = now - last_change_at
            ceiling_elapsed = now - phase_entered_at
            if stuck_elapsed >= budget.stuck_seconds:
                raise ProvisionError(
                    ProvisionReason.TIMEOUT.value,
                    f"Instance {vastai_id} stuck in {current_state.value} — no signal change for {stuck_elapsed:.0f}s",
                )
            if ceiling_elapsed >= budget.ceiling_seconds:
                raise ProvisionError(
                    ProvisionReason.TIMEOUT.value,
                    f"Instance {vastai_id} exceeded {budget.ceiling_seconds}s ceiling in {current_state.value}",
                )

            await emit(actual_status or "loading")
            await asyncio.sleep(poll_interval)

    async def _connect_and_launch(
        self, record: ProvisionedInstance, username: str, launch_env: dict | None, status_callback, start: float
    ) -> InstanceAssignment:
        vastai_id = record.vastai_instance_id
        current = LifecycleState(record.lifecycle_state)
        # A shared instance already IDLE/ACTIVE has its key attached and (usually)
        # a live cached SSH connection already — an additional/returning user only
        # needs a fresh Blender launch, not the full attach+connect handshake.
        already_up = current in (LifecycleState.IDLE, LifecycleState.ACTIVE)

        async def emit(status: str):
            if status_callback:
                try:
                    await status_callback(status, int(time.time() - start))
                except Exception:
                    pass

        if not already_up:
            # Attach the SSH key now that the container is confirmed running —
            # VastAI only applies it to a live container.
            await self.repo.transition(vastai_id, LifecycleState.SSH_KEY_ATTACHING)
            await emit("ssh_key_attaching")
            key_attached = await self.vastai.attach_ssh_key(vastai_id)
            if not key_attached:
                raise ProvisionError(ProvisionReason.SSH_FAILED.value, f"SSH key attachment failed for instance {vastai_id}")
            await self.repo.transition(vastai_id, LifecycleState.SSH_CONNECTING)

        await emit("ssh_connecting")
        try:
            # get_connection reuses a live cached connection or retries with
            # exponential backoff internally — this replaces the legacy blind
            # sleep(5)/sleep(15) propagation delay with an actual readiness check.
            await self.ssh.get_connection(vastai_id, record.host, record.ssh_port)
        except Exception as e:
            raise ProvisionError(ProvisionReason.SSH_FAILED.value, f"SSH connection failed to instance {vastai_id}: {e}")

        if not already_up:
            await self.repo.transition(vastai_id, LifecycleState.BLENDER_LAUNCHING)
        await emit("blender_starting")

        async def ssh_cb(status: str):
            await emit(f"blender:{status}")

        try:
            from app.auth.internal_token import generate_blender_token

            auth_token = generate_blender_token(username)
            pid = await self.ssh.launch_blender(
                vastai_id, username, status_callback=ssh_cb, auth_token=auth_token, launch_env=launch_env
            )
        except LaunchError as e:
            if any(p in e.error_code for p in INSTANCE_FATAL_PATTERNS):
                # Genuinely broken hardware/driver (xorg/nvidia) — this
                # specific machine is unusable, no amount of retrying Blender
                # itself will fix it.
                raise ProvisionError(ProvisionReason.INSTANCE_INCOMPATIBLE.value, str(e), instance_fatal=True)
            # Everything else here happens with the VastAI machine already
            # confirmed alive (we're past _wait_for_vast_ready) — a hung or
            # crashed Blender process is a software hiccup, not a reason to
            # throw away a paid-for GPU instance. instance_fatal=False lets
            # _fail_attempt recover it to IDLE instead of destroying it.
            if e.error_code == "timeout":
                raise ProvisionError(ProvisionReason.TIMEOUT.value, str(e), instance_fatal=False)
            # Surface known CR8:ERROR codes directly when they're in our closed
            # taxonomy; anything else folds into the generic BLENDER_FAILED.
            reason = e.error_code if e.error_code in {r.value for r in ProvisionReason} else ProvisionReason.BLENDER_FAILED.value
            raise ProvisionError(reason, str(e), instance_fatal=False)
        except Exception as e:
            raise ProvisionError(
                ProvisionReason.BLENDER_FAILED.value, f"Blender launch failed on instance {vastai_id}: {e}", instance_fatal=False
            )

        await self.repo.transition(vastai_id, LifecycleState.ACTIVE)
        await self.repo.start_session(vastai_id, username, pid)

        return InstanceAssignment(
            instance_id=vastai_id, host=record.host, ssh_port=record.ssh_port, gpu_name=record.gpu_name, blender_pid=pid
        )
