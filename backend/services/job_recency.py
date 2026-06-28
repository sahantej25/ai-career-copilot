"""Filter and sort job listings by how recently they were posted."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal

from models.schemas import CandidateProfile, JobListing
from services.job_dates import has_published_at, parse_published_at, published_at_timestamp

PostedWithin = Literal["24h", "3d", "7d", "anytime"]

# Single source of truth for upstream fetch windows (Hiring Cafe API, etc.)
MAX_JOB_FETCH_DAYS = 14

POSTED_WITHIN_OPTIONS: tuple[tuple[PostedWithin, str, int | None], ...] = (
    ("24h", "Last 24 hours", 1),
    ("3d", "Last 3 days", 3),
    ("7d", "Last week", 7),
    ("anytime", "Anytime", None),
)

_VALID: frozenset[str] = frozenset(v for v, _, _ in POSTED_WITHIN_OPTIONS)

_RECENCY_HOURS: dict[PostedWithin, int] = {
    "24h": 24,
    "3d": 72,
    "7d": 168,
}


def normalize_posted_within(value: str | None) -> PostedWithin:
    normalized = (value or "anytime").strip().lower()
    if normalized in _VALID:
        return normalized  # type: ignore[return-value]
    return "anytime"


def max_job_fetch_days() -> int:
    """Days to request from upstream aggregators — always the widest practical window."""
    return MAX_JOB_FETCH_DAYS


def posted_within_to_days(value: str | None) -> int:
    """Backward-compatible alias for upstream fetch day window."""
    return max_job_fetch_days()


def recency_cutoff(posted_within: str, *, now: datetime | None = None) -> datetime | None:
    window = normalize_posted_within(posted_within)
    if window == "anytime":
        return None
    reference = now or datetime.now(timezone.utc)
    hours = _RECENCY_HOURS[window]
    return reference - timedelta(hours=hours)


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

    published = parse_published_at(job.published_at, reference=now)
    if published is None:
        # Without a verified posted date, only include in "anytime".
        return False

    cutoff = recency_cutoff(window, now=now)
    assert cutoff is not None
    return published >= cutoff


def filter_jobs_by_recency(
    jobs: list[JobListing],
    posted_within: str,
    *,
    now: datetime | None = None,
) -> list[JobListing]:
    window = normalize_posted_within(posted_within)
    if window == "anytime":
        return list(jobs)
    return [j for j in jobs if job_within_recency(j, window, now=now)]


def sort_jobs_for_display(
    jobs: list[JobListing],
    *,
    profile: CandidateProfile | None = None,
) -> list[JobListing]:
    """Newest posted first; undated listings sink to the bottom."""

    def sort_key(job: JobListing) -> tuple[float, float, str]:
        posted_ts = published_at_timestamp(job.published_at)
        match = float(job.match_percentage or 0) if profile else 0.0
        # Undated jobs (posted_ts=0) sort after dated jobs.
        dated_rank = 1.0 if has_published_at(job.published_at) else 0.0
        return (dated_rank, posted_ts, match)

    return sorted(jobs, key=sort_key, reverse=True)
