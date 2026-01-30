"""Simple in-memory rate limiter with sliding window."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
import time


class SlidingWindowRateLimiter:
    """Rate limiter using a sliding window per key."""

    def __init__(
        self,
        max_calls: int,
        window_seconds: int,
        time_fn: Callable[[], float] | None = None,
    ) -> None:
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self._time_fn = time_fn or time.monotonic
        self._buckets: dict[str, deque[float]] = {}

    def allow(self, key: str) -> bool:
        """Check and record whether a call is allowed for the key."""
        now = self._time_fn()
        window_start = now - self.window_seconds
        bucket = self._buckets.setdefault(key, deque())

        while bucket and bucket[0] <= window_start:
            bucket.popleft()

        if len(bucket) >= self.max_calls:
            return False

        bucket.append(now)
        return True
