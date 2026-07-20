"""
Cancellation registry for in-flight provisioning attempts.

Fixes the legacy cancellation gap: `release_user()` required a UserSession,
which only existed after SSH+Blender succeeded, so cancelling during the slow
VastAI-provisioning phase was a complete no-op and the background task just
kept running to completion regardless.

Usage: `provision_for_user()` wraps its whole body in an asyncio.Task and
registers it here *synchronously, before the task's first await* — closing
the race where a cancel could arrive before registration is visible.
`on_cancel_launch` looks the task up and cancels it directly, so
`wait_for_ready`/SSH-connect/etc. are actually interrupted at their next
await point, instead of running unattended in the background.

This registry is a responsiveness fast-path only. Correctness (the instance
actually getting torn down) never depends on cancellation completing cleanly
here — the continuous reconciler is the real backstop even if the process
dies mid-cancel.
"""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ProvisionAttemptRegistry:
    def __init__(self):
        self._tasks: dict[str, asyncio.Task] = {}

    def register(self, username: str, task: asyncio.Task) -> None:
        self._tasks[username] = task
        task.add_done_callback(lambda t, u=username: self._on_done(u, t))

    def _on_done(self, username: str, task: asyncio.Task) -> None:
        # Only clear the slot if it's still this exact task — a new attempt may
        # have already registered under the same username by the time this fires.
        if self._tasks.get(username) is task:
            del self._tasks[username]

    def get(self, username: str) -> Optional[asyncio.Task]:
        return self._tasks.get(username)

    def cancel(self, username: str) -> bool:
        """Requests cancellation of the in-flight attempt for `username`, if any.
        Returns True if a task was found and cancel() was requested (delivery is
        async — the task isn't necessarily stopped by the time this returns)."""
        task = self._tasks.get(username)
        if task is None or task.done():
            return False
        logger.info(f"Cancelling in-flight provisioning attempt for {username}")
        task.cancel()
        return True


_registry: Optional[ProvisionAttemptRegistry] = None


def get_registry() -> ProvisionAttemptRegistry:
    global _registry
    if _registry is None:
        _registry = ProvisionAttemptRegistry()
    return _registry
