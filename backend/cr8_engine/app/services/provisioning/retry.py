"""
One shared exponential-backoff-with-jitter retry helper, replacing the three
independent bespoke flat-delay loops in the legacy code (ssh_service.get_connection,
vastai_service.launch_instance's inline 429 handling, manager._launch_and_assign's
attempt loop).
"""

import asyncio
import logging
import random
from typing import Awaitable, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def retry_with_backoff(
    fn: Callable[[], Awaitable[T]],
    *,
    max_attempts: int,
    base_delay: float,
    factor: float = 2.0,
    max_delay: float | None = None,
    jitter: bool = True,
    retry_on: tuple[type[BaseException], ...] = (Exception,),
    on_retry: Callable[[int, BaseException], None] | None = None,
) -> T:
    """Calls `fn()` up to max_attempts times. Raises the last exception if every
    attempt fails. Delay grows as base_delay * factor**attempt, capped at
    max_delay, with +/-25% jitter unless disabled."""
    last_exc: BaseException | None = None
    for attempt in range(max_attempts):
        try:
            return await fn()
        except retry_on as e:
            last_exc = e
            if attempt >= max_attempts - 1:
                break
            delay = base_delay * (factor**attempt)
            if max_delay is not None:
                delay = min(delay, max_delay)
            if jitter:
                delay *= random.uniform(0.75, 1.25)
            if on_retry:
                try:
                    on_retry(attempt, e)
                except Exception:
                    pass
            logger.warning(f"Attempt {attempt + 1}/{max_attempts} failed ({e}); retrying in {delay:.1f}s")
            await asyncio.sleep(delay)
    assert last_exc is not None
    raise last_exc
