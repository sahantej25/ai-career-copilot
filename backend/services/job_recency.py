"""Filter job listings by how recently they were posted."""
from datetime import datetime, timedelta, timezone
from typing import Literal

from models.schemas import JobListing

PostedWithin = Literal["24h", "3d", "7d", "anytime"]

POSTED_WITHIN_OPTIONS: tuple[tuple[PostedWithin, str, int | None], ...] = (
    ("24h", "Last 24 hours", 1),
    ("3d", "Last 3 days", 3),
    ("7d", "Last week", 7),
    ("anytime", "Anytime", None),
)

_VALID: frozenset[str] = frozenset(v for v, _, _ in POSTED_WITHIN_OPTIONS)


def normalize_posted_within(value: str | None) -> PostedWithin:
    normalized = (value or "anytime").strip().lower()
    if normalized in _VALID:
        return normalized  # type: ignore[return-value]
    return "anytime"


def posted_within_to_days(value: str | None) -> int:
    """Map preference to Hiring Cafe API `dateFetchedPastNDays` (minimum 1)."""
    mapping = {"24h": 1, "3d": 3, "7d": 7, "anytime": 14}
    return mapping.get(normalize_posted_within(value), 14)


def _parse_published_at(raw: str) -> datetime | None:
    text = (raw or "").strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            return datetime.fromisoformat(text.replace("Z", "+00:00"))
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def job_within_recency(
    job: JobListing,
    posted_within: str,
    *,
    now: datetime | None = None,
) -> bool:
    """Return True if job falls within the selected recency window."""
    window = normalize_posted_within(posted_within)
    if window == "anytime":
        return True

    hours = {"24h": 24, "3d": 72, "7d": 168}[window]
    reference = now or datetime.now(timezone.utc)
    cutoff = reference - timedelta(hours=hours)

    published = _parse_published_at(job.published_at)
    if published is None:
        # Sources like LinkedIn guest search don't expose dates — keep in results.
        return True
    return published >= cutoff


def filter_jobs_by_recency(
    jobs: list[JobListing],
    posted_within: str,
    *,
    now: datetime | None = None,
) -> list[JobListing]:
    window = normalize_posted_within(posted_within)
    if window == "anytime":
        return jobs
    return [j for j in jobs if job_within_recency(j, window, now=now)]
