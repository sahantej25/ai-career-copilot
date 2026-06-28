"""Tests for job recency filtering."""
from datetime import datetime, timedelta, timezone

from models.schemas import JobListing
from services.job_recency import (
    filter_jobs_by_recency,
    job_within_recency,
    normalize_posted_within,
    posted_within_to_days,
)


def _job(published_at: str) -> JobListing:
    return JobListing(
        id="greenhouse:test:1",
        title="Engineer",
        company="Acme",
        published_at=published_at,
        apply_url="https://example.com/apply",
        source="greenhouse",
    )


def test_normalize_posted_within_defaults_invalid():
    assert normalize_posted_within("bad") == "anytime"
    assert normalize_posted_within("24h") == "24h"


def test_posted_within_to_days_mapping():
    assert posted_within_to_days("24h") == 1
    assert posted_within_to_days("3d") == 3
    assert posted_within_to_days("7d") == 7
    assert posted_within_to_days("anytime") == 14


def test_job_within_recency_24h():
    now = datetime(2026, 6, 27, 12, 0, tzinfo=timezone.utc)
    recent = (now - timedelta(hours=12)).isoformat().replace("+00:00", "Z")
    old = (now - timedelta(days=5)).isoformat().replace("+00:00", "Z")

    assert job_within_recency(_job(recent), "24h", now=now) is True
    assert job_within_recency(_job(old), "24h", now=now) is False
    assert job_within_recency(_job(""), "24h", now=now) is True  # undated kept


def test_filter_jobs_by_recency():
    now = datetime(2026, 6, 27, 12, 0, tzinfo=timezone.utc)
    recent = (now - timedelta(days=1)).isoformat().replace("+00:00", "Z")
    old = (now - timedelta(days=10)).isoformat().replace("+00:00", "Z")
    jobs = [_job(recent), _job(old)]

    filtered = filter_jobs_by_recency(jobs, "7d", now=now)
    assert len(filtered) == 1
    assert filtered[0].published_at == recent

    assert len(filter_jobs_by_recency(jobs, "anytime", now=now)) == 2
