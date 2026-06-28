"""In-memory per-user rate limiter for AI endpoints."""
import asyncio
import time
from collections import defaultdict

from fastapi import HTTPException

from config import settings
from services.guardrails.constants import AI_RATE_LIMIT_REQUESTS, AI_RATE_LIMIT_WINDOW_SECONDS

_lock = asyncio.Lock()
_buckets: dict[str, list[float]] = defaultdict(list)


def _limits() -> tuple[int, int]:
    return (
        getattr(settings, "ai_rate_limit_requests", AI_RATE_LIMIT_REQUESTS),
        getattr(settings, "ai_rate_limit_window_seconds", AI_RATE_LIMIT_WINDOW_SECONDS),
    )


async def check_ai_rate_limit(user_id: str) -> None:
    """Raise 429 if user exceeded AI call quota for the current window."""
    max_requests, window_seconds = _limits()
    now = time.monotonic()
    cutoff = now - window_seconds

    async with _lock:
        hits = [t for t in _buckets[user_id] if t > cutoff]
        if len(hits) >= max_requests:
            raise HTTPException(
                429,
                f"AI request limit reached ({max_requests} per hour). "
                "Please wait before trying again.",
            )
        hits.append(now)
        _buckets[user_id] = hits


def reset_rate_limits() -> None:
    """Test helper — clear all buckets."""
    _buckets.clear()
