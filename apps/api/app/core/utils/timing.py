import time
from collections.abc import Iterator
from contextlib import contextmanager


@contextmanager
def stopwatch() -> Iterator[dict[str, float]]:
    """`with stopwatch() as t: ...` then read `t["ms"]`."""
    result: dict[str, float] = {}
    start = time.perf_counter()
    try:
        yield result
    finally:
        result["ms"] = round((time.perf_counter() - start) * 1000, 1)
