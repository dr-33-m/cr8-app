"""
Guaranteed-destroy loop — the load-bearing piece of this whole re-architecture.

Protocol: a teardown_intents row is written BEFORE any destroy is attempted
(by orchestrator.py or reconciler.py), and this worker is the only thing that
ever marks one confirmed. It never trusts a single destroy_instance() boolean
return — it re-polls get_instance_info() until the instance is actually gone
(terminal actual_status, or a 404/None response), retrying with backoff
FOREVER on anything else. There is no give-up path: an open intent either
gets confirmed or shows up in list_stuck_teardown_intents() as a loud,
logged signal instead of decaying silently.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from .config import ProvisioningConfig
from .repository import ProvisioningRepository
from .state_machine import LifecycleState, IllegalTransitionError, is_terminal
from .vastai_client import VastAIClient

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TeardownWorker:
    def __init__(self, vastai: VastAIClient, repo: ProvisioningRepository):
        self.vastai = vastai
        self.repo = repo
        self.config = ProvisioningConfig.get()

    async def run_forever(self):
        logger.info("Teardown worker started")
        while True:
            try:
                await self.run_once()
            except asyncio.CancelledError:
                logger.info("Teardown worker cancelled")
                raise
            except Exception:
                logger.exception("Teardown worker pass failed unexpectedly")
            await asyncio.sleep(5)

    async def run_once(self):
        intents = await self.repo.list_due_teardown_intents()
        for intent in intents:
            await self._process(intent)

        stuck = await self.repo.list_stuck_teardown_intents(
            self.config.TEARDOWN_STUCK_ATTEMPTS_ALERT, self.config.TEARDOWN_STUCK_AGE_SECONDS
        )
        for s in stuck:
            logger.critical(
                f"Teardown intent {s.id} for instance {s.vastai_instance_id} is stuck: "
                f"{s.attempts} attempts, reason={s.reason}, last_error={s.last_error}"
            )

    async def _process(self, intent) -> None:
        vastai_id = intent.vastai_instance_id
        try:
            await self.repo.mark_teardown_requested(intent.id)
            await self._ensure_destroying(vastai_id)
            await self.vastai.destroy_instance(vastai_id)

            info = await self.vastai.get_instance_info(vastai_id)
            if info is None:
                await self.repo.mark_teardown_confirmed(intent.id, "confirmed_absent")
                await self._ensure_destroyed(vastai_id)
                return

            if is_terminal(info.get("actual_status"), info.get("intended_status"), info.get("next_state")):
                await self.repo.mark_teardown_confirmed(intent.id, "confirmed_destroyed")
                await self._ensure_destroyed(vastai_id)
                return

            raise RuntimeError(f"instance {vastai_id} not yet terminal (actual_status={info.get('actual_status')})")

        except Exception as e:
            delay = min(
                self.config.TEARDOWN_BASE_DELAY_SECONDS * (self.config.TEARDOWN_BACKOFF_FACTOR**intent.attempts),
                self.config.TEARDOWN_MAX_DELAY_SECONDS,
            )
            next_attempt_at = _utcnow() + timedelta(seconds=delay)
            await self.repo.mark_teardown_retry(intent.id, next_attempt_at, str(e))
            logger.warning(f"Teardown intent {intent.id} (instance {vastai_id}) not confirmed yet, retry in {delay:.0f}s: {e}")

    async def _ensure_destroying(self, vastai_id: int) -> None:
        record = await self.repo.get_instance(vastai_id)
        if record is None or record.lifecycle_state in (LifecycleState.DESTROYING.value, LifecycleState.DESTROYED.value):
            return
        try:
            await self.repo.transition(vastai_id, LifecycleState.DESTROYING)
        except IllegalTransitionError:
            logger.warning(f"Could not transition instance {vastai_id} to DESTROYING from {record.lifecycle_state}")

    async def _ensure_destroyed(self, vastai_id: int) -> None:
        record = await self.repo.get_instance(vastai_id)
        if record is None or record.lifecycle_state == LifecycleState.DESTROYED.value:
            return
        try:
            await self.repo.transition(vastai_id, LifecycleState.DESTROYED)
        except IllegalTransitionError:
            await self._ensure_destroying(vastai_id)
            await self.repo.transition(vastai_id, LifecycleState.DESTROYED)
