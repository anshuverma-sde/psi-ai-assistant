import asyncio
import logging
import random
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")
logger = logging.getLogger(__name__)


async def retry_async(
    fn: Callable[[], Awaitable[T]],
    *,
    attempts: int,
    retry_on: tuple[type[BaseException], ...],
    base_delay: float = 0.6,
    max_delay: float = 6.0,
    label: str = "operation",
) -> T:
    """Retries `fn` with exponential backoff + jitter on the given exception types."""
    for attempt in range(1, attempts + 1):
        try:
            return await fn()
        except retry_on as exc:
            if attempt == attempts:
                raise
            delay = min(max_delay, base_delay * 2 ** (attempt - 1)) + random.uniform(0, 0.3)
            logger.warning("%s failed (attempt %s/%s): %s — retrying in %.1fs",
                           label, attempt, attempts, exc, delay)
            await asyncio.sleep(delay)
    raise RuntimeError("unreachable")  # pragma: no cover
