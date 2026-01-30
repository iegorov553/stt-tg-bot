"""Tests for rate limiter utility."""

from stt_tg_bot.utils.rate_limiter import SlidingWindowRateLimiter


def test_rate_limiter_allows_within_window() -> None:
    """Allow up to max calls within window."""
    times = iter([0.0, 1.0, 2.0])

    def now() -> float:
        return next(times)

    limiter = SlidingWindowRateLimiter(max_calls=2, window_seconds=60, time_fn=now)

    assert limiter.allow("user") is True
    assert limiter.allow("user") is True
    assert limiter.allow("user") is False


def test_rate_limiter_resets_after_window() -> None:
    """Old calls should expire after the window passes."""
    times = iter([0.0, 1.0, 61.0, 62.0])

    def now() -> float:
        return next(times)

    limiter = SlidingWindowRateLimiter(max_calls=2, window_seconds=60, time_fn=now)

    assert limiter.allow("user") is True
    assert limiter.allow("user") is True
    assert limiter.allow("user") is True
    assert limiter.allow("user") is True


def test_rate_limiter_is_per_key() -> None:
    """Each key should have an independent bucket."""
    times = iter([0.0, 0.0, 0.0])

    def now() -> float:
        return next(times)

    limiter = SlidingWindowRateLimiter(max_calls=1, window_seconds=60, time_fn=now)

    assert limiter.allow("user-a") is True
    assert limiter.allow("user-b") is True
    assert limiter.allow("user-a") is False
