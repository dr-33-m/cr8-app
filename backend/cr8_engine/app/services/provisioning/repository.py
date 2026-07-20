"""
Async repository over the provisioning Postgres tables. This is the only
place that talks SQL for the new system — orchestrator/teardown_worker/
reconciler all go through here, never raw sessions, so the durability
invariants (idempotent teardown enqueue, legal-transition enforcement) are
enforced in exactly one place.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.engine import get_session_factory
from .models import ProvisionedInstance, InstanceUserSession, TeardownIntent, ProvisioningEvent, FastLaunchMachine
from .state_machine import LifecycleState, assert_legal_transition
from .errors import TeardownReason

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ProvisioningRepository:
    """Async CRUD/upsert layer. Each public method manages its own short-lived
    session/transaction unless noted — callers never see a raw AsyncSession."""

    def __init__(self, session_maker: Optional[async_sessionmaker] = None):
        # session_maker overrides the default DB (used by tests against a
        # throwaway engine); left None it lazily resolves the app's singleton
        # factory on first use so constructing a repository never requires a
        # live DB connection.
        self._session_maker = session_maker

    def _session(self) -> AsyncSession:
        maker = self._session_maker or get_session_factory()
        return maker()

    # --- Instances ---

    async def create_instance(
        self,
        vastai_id: int,
        gpu_name: str,
        max_users: int,
        lifecycle_state: LifecycleState = LifecycleState.REQUESTED,
        adopted: bool = False,
        machine_id: Optional[int] = None,
    ) -> ProvisionedInstance:
        async with self._session() as session:
            record = ProvisionedInstance(
                vastai_instance_id=vastai_id,
                gpu_name=gpu_name,
                max_users=max_users,
                lifecycle_state=lifecycle_state.value,
                adopted=adopted,
                machine_id=machine_id,
                last_state_change_at=_utcnow(),
            )
            session.add(record)
            await session.commit()
            await session.refresh(record)
            return record

    async def get_instance(self, vastai_id: int) -> Optional[ProvisionedInstance]:
        async with self._session() as session:
            return await session.get(ProvisionedInstance, vastai_id)

    async def list_active_instances(self) -> list[ProvisionedInstance]:
        """All instances not yet confirmed DESTROYED — the reconciler's working set."""
        async with self._session() as session:
            result = await session.execute(
                select(ProvisionedInstance).where(
                    ProvisionedInstance.lifecycle_state != LifecycleState.DESTROYED.value
                )
            )
            return list(result.scalars().all())

    async def find_available_instance(self, gpu_name: str, max_users: int) -> Optional[ProvisionedInstance]:
        """A reusable IDLE/ACTIVE instance with the right GPU and spare capacity —
        the shared-instance reuse path's equivalent of the legacy
        find_available_instance. `max_users` is passed by the caller
        (DeploymentConfig.MAX_USERS_PER_INSTANCE) rather than trusted per-row,
        since it's a fleet-wide policy, not a per-instance one."""
        async with self._session() as session:
            result = await session.execute(
                select(ProvisionedInstance).where(
                    ProvisionedInstance.gpu_name == gpu_name,
                    ProvisionedInstance.lifecycle_state.in_([LifecycleState.IDLE.value, LifecycleState.ACTIVE.value]),
                )
            )
            candidates = list(result.scalars().all())
            for candidate in candidates:
                count_result = await session.execute(
                    select(InstanceUserSession).where(
                        InstanceUserSession.vastai_instance_id == candidate.vastai_instance_id,
                        InstanceUserSession.ended_at.is_(None),
                    )
                )
                active_count = len(count_result.scalars().all())
                if active_count < max_users:
                    return candidate
            return None

    async def transition(
        self,
        vastai_id: int,
        target: LifecycleState,
        *,
        error_reason: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> ProvisionedInstance:
        async with self._session() as session:
            record = await session.get(ProvisionedInstance, vastai_id)
            if record is None:
                raise ValueError(f"No provisioned_instances row for {vastai_id}")
            current = LifecycleState(record.lifecycle_state)
            assert_legal_transition(current, target)
            record.lifecycle_state = target.value
            if error_reason is not None:
                record.last_error_reason = error_reason
            if error_message is not None:
                record.last_error_message = error_message
            if target == LifecycleState.DESTROYED:
                record.destroyed_at = _utcnow()
            session.add(
                ProvisioningEvent(
                    vastai_instance_id=vastai_id,
                    event_type="state_transition",
                    detail={"from": current.value, "to": target.value, "reason": error_reason},
                )
            )
            await session.commit()
            await session.refresh(record)
            return record

    async def update_signals(
        self,
        vastai_id: int,
        actual_status: Optional[str],
        cur_state: Optional[str],
        intended_status: Optional[str],
        next_state: Optional[str],
    ) -> tuple[ProvisionedInstance, bool]:
        """Records the raw signal tuple. Returns (record, changed) — changed is
        True only if (actual_status, cur_state, next_state) differs from what
        was stored, which is what drives stuck-detection upstream."""
        async with self._session() as session:
            record = await session.get(ProvisionedInstance, vastai_id)
            if record is None:
                raise ValueError(f"No provisioned_instances row for {vastai_id}")
            prev_tuple = (record.vastai_actual_status, record.vastai_cur_state, record.vastai_next_state)
            new_tuple = (actual_status, cur_state, next_state)
            changed = prev_tuple != new_tuple
            record.vastai_actual_status = actual_status
            record.vastai_cur_state = cur_state
            record.vastai_intended_status = intended_status
            record.vastai_next_state = next_state
            record.last_polled_at = _utcnow()
            if changed:
                record.last_state_change_at = _utcnow()
            await session.commit()
            await session.refresh(record)
            return record, changed

    async def set_connection_info(self, vastai_id: int, host: str, ssh_port: int) -> None:
        async with self._session() as session:
            await session.execute(
                update(ProvisionedInstance)
                .where(ProvisionedInstance.vastai_instance_id == vastai_id)
                .values(host=host, ssh_port=ssh_port)
            )
            await session.commit()

    async def set_phase_detail(self, vastai_id: int, phase_detail: str) -> None:
        async with self._session() as session:
            await session.execute(
                update(ProvisionedInstance)
                .where(ProvisionedInstance.vastai_instance_id == vastai_id)
                .values(phase_detail=phase_detail)
            )
            await session.commit()

    # --- Teardown ledger ---

    async def enqueue_teardown(self, vastai_id: int, reason: TeardownReason) -> bool:
        """Idempotent: inserting against an already-open intent (status not in
        confirmed_*) is a no-op. Returns True if a new intent was actually
        created.

        Check-then-insert rather than `ON CONFLICT ... WHERE ... DO NOTHING`:
        the latter depends on Postgres matching the statement's arbiter
        predicate against ux_open_teardown_per_instance by inference, which
        turned out to be fragile across environments in practice (observed
        failing in production with `InvalidColumnReferenceError: there is no
        unique or exclusion constraint matching the ON CONFLICT specification`
        despite passing against the migration-created index in tests —
        possibly SQLAlchemy/asyncpg version drift, since both are unpinned in
        requirements.txt). This is the single most billing-safety-critical
        write in the system, so it must not depend on that inference matching
        correctly. The IntegrityError fallback below still makes concurrent
        callers race-safe if the partial unique index IS present; if it's
        somehow not, this degrades to check-then-insert with a narrow race
        window rather than failing outright on every call."""
        existing = await self.get_open_teardown(vastai_id)
        if existing is not None:
            await self.record_event(
                "teardown_enqueue_deduped", vastai_instance_id=vastai_id, detail={"reason": reason.value}
            )
            return False

        async with self._session() as session:
            record = TeardownIntent(vastai_instance_id=vastai_id, reason=reason.value)
            session.add(record)
            try:
                await session.flush()
            except IntegrityError:
                # Lost a race against a concurrent enqueue for the same instance.
                await session.rollback()
                async with self._session() as dedup_session:
                    dedup_session.add(
                        ProvisioningEvent(
                            vastai_instance_id=vastai_id,
                            event_type="teardown_enqueue_deduped",
                            detail={"reason": reason.value, "raced": True},
                        )
                    )
                    await dedup_session.commit()
                return False

            session.add(
                ProvisioningEvent(
                    vastai_instance_id=vastai_id, event_type="teardown_enqueued", detail={"reason": reason.value}
                )
            )
            await session.commit()

        logger.warning(f"Teardown intent enqueued for instance {vastai_id}: {reason.value}")
        return True

    async def list_due_teardown_intents(self, limit: int = 50) -> list[TeardownIntent]:
        async with self._session() as session:
            result = await session.execute(
                select(TeardownIntent)
                .where(
                    TeardownIntent.status.in_(["pending", "destroy_requested"]),
                    TeardownIntent.next_attempt_at <= _utcnow(),
                )
                .order_by(TeardownIntent.next_attempt_at)
                .limit(limit)
            )
            return list(result.scalars().all())

    async def list_stuck_teardown_intents(self, min_attempts: int, min_age_seconds: int) -> list[TeardownIntent]:
        """Open intents that have been retried a lot or sat open a long time —
        the loud signal that replaces silent decay."""
        cutoff = _utcnow() - timedelta(seconds=min_age_seconds)
        async with self._session() as session:
            result = await session.execute(
                select(TeardownIntent).where(
                    TeardownIntent.status.in_(["pending", "destroy_requested"]),
                    (TeardownIntent.attempts >= min_attempts) | (TeardownIntent.created_at <= cutoff),
                )
            )
            return list(result.scalars().all())

    async def mark_teardown_requested(self, intent_id) -> None:
        async with self._session() as session:
            await session.execute(
                update(TeardownIntent).where(TeardownIntent.id == intent_id).values(status="destroy_requested")
            )
            await session.commit()

    async def mark_teardown_retry(self, intent_id, next_attempt_at: datetime, error: str) -> None:
        async with self._session() as session:
            intent = await session.get(TeardownIntent, intent_id)
            if intent is None:
                return
            intent.attempts += 1
            intent.next_attempt_at = next_attempt_at
            intent.last_error = error[:2000] if error else None
            await session.commit()

    async def mark_teardown_confirmed(self, intent_id, confirmed_status: str) -> None:
        assert confirmed_status in ("confirmed_destroyed", "confirmed_absent")
        async with self._session() as session:
            intent = await session.get(TeardownIntent, intent_id)
            if intent is None:
                return
            intent.status = confirmed_status
            intent.confirmed_at = _utcnow()
            await session.commit()

    async def get_open_teardown(self, vastai_id: int) -> Optional[TeardownIntent]:
        async with self._session() as session:
            result = await session.execute(
                select(TeardownIntent).where(
                    TeardownIntent.vastai_instance_id == vastai_id,
                    TeardownIntent.status.notin_(["confirmed_destroyed", "confirmed_absent"]),
                )
            )
            return result.scalars().first()

    # --- User sessions ---

    async def start_session(self, vastai_id: int, username: str, blender_pid: int) -> InstanceUserSession:
        async with self._session() as session:
            # Defensively close any stale open session for this user before opening
            # a new one — the unique partial index would otherwise reject the insert.
            await session.execute(
                update(InstanceUserSession)
                .where(InstanceUserSession.username == username, InstanceUserSession.ended_at.is_(None))
                .values(ended_at=_utcnow())
            )
            record = InstanceUserSession(vastai_instance_id=vastai_id, username=username, blender_pid=blender_pid)
            session.add(record)
            await session.commit()
            await session.refresh(record)
            return record

    async def end_session(self, username: str) -> Optional[int]:
        """Ends the user's active session, returns its instance id (or None)."""
        async with self._session() as session:
            result = await session.execute(
                select(InstanceUserSession).where(
                    InstanceUserSession.username == username, InstanceUserSession.ended_at.is_(None)
                )
            )
            record = result.scalars().first()
            if record is None:
                return None
            record.ended_at = _utcnow()
            instance_id = record.vastai_instance_id
            await session.commit()
            return instance_id

    async def get_active_session(self, username: str) -> Optional[InstanceUserSession]:
        async with self._session() as session:
            result = await session.execute(
                select(InstanceUserSession).where(
                    InstanceUserSession.username == username, InstanceUserSession.ended_at.is_(None)
                )
            )
            return result.scalars().first()

    async def get_idle_since(self, vastai_id: int) -> Optional[datetime]:
        """Timestamp the instance became idle — the most recent session end for
        it, or None if it has never had a session end (shouldn't happen for an
        instance actually in IDLE, since IDLE is only reached via a session
        ending, but callers should treat None defensively as 'not idle yet')."""
        async with self._session() as session:
            result = await session.execute(
                select(InstanceUserSession.ended_at)
                .where(InstanceUserSession.vastai_instance_id == vastai_id, InstanceUserSession.ended_at.isnot(None))
                .order_by(InstanceUserSession.ended_at.desc())
                .limit(1)
            )
            return result.scalar_one_or_none()

    async def list_active_sessions(self, vastai_id: int) -> list[InstanceUserSession]:
        async with self._session() as session:
            result = await session.execute(
                select(InstanceUserSession).where(
                    InstanceUserSession.vastai_instance_id == vastai_id,
                    InstanceUserSession.ended_at.is_(None),
                )
            )
            return list(result.scalars().all())

    # --- Fast-launch ledger ---

    async def record_fast_launch(self, machine_id: int, gpu_name: str, seconds: int, vastai_instance_id: int) -> None:
        """Upsert: a machine only ever improves its best_launch_seconds and
        accumulates fast_launch_count — a single slower-but-still-fast launch
        later doesn't erase a previously-proven faster time."""
        async with self._session() as session:
            existing = await session.get(FastLaunchMachine, machine_id)
            if existing is None:
                session.add(
                    FastLaunchMachine(
                        machine_id=machine_id,
                        gpu_name=gpu_name,
                        best_launch_seconds=seconds,
                        fast_launch_count=1,
                        last_vastai_instance_id=vastai_instance_id,
                        last_fast_launch_at=_utcnow(),
                    )
                )
            else:
                existing.gpu_name = gpu_name
                existing.best_launch_seconds = min(existing.best_launch_seconds, seconds)
                existing.fast_launch_count += 1
                existing.last_vastai_instance_id = vastai_instance_id
                existing.last_fast_launch_at = _utcnow()
            await session.commit()
        logger.info(f"Recorded fast launch: machine {machine_id} ({gpu_name}) in {seconds}s")

    async def list_fast_machine_ids(self, gpu_name: str, limit: int = 10) -> list[int]:
        """Known-fast machines for this GPU tier, fastest first — what
        orchestrator.py's offer search tries before the general search."""
        async with self._session() as session:
            result = await session.execute(
                select(FastLaunchMachine.machine_id)
                .where(FastLaunchMachine.gpu_name == gpu_name)
                .order_by(FastLaunchMachine.best_launch_seconds.asc())
                .limit(limit)
            )
            return [row[0] for row in result.all()]

    # --- Events / audit ---

    async def record_event(
        self,
        event_type: str,
        vastai_instance_id: Optional[int] = None,
        username: Optional[str] = None,
        detail: Optional[dict] = None,
    ) -> None:
        async with self._session() as session:
            session.add(
                ProvisioningEvent(
                    vastai_instance_id=vastai_instance_id,
                    username=username,
                    event_type=event_type,
                    detail=detail or {},
                )
            )
            await session.commit()
