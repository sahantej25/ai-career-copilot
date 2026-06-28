"""Tests for job recency filtering."""
from datetime import datetime, timedelta, timezone

from models.schemas import JobListing
from services.job_recency import (
    filter_jobs_by_recency,
    job_within_recency,
    max_job_fetch_days,
    normalize_posted_within,
    posted_within_to_days,
    sort_jobs_for_display,
)


def _job(published_at: str, job_id: str = "greenhouse:test:1") -> JobListing:
    return JobListing(
        id=job_id,
        title="Engineer",
        company="Acme",
        published_at=published_at,
        apply_url="https://example.com/apply",
        source="greenhouse",
    )


def test_normalize_posted_within_defaults_invalid():
    assert normalize_posted_within("bad") == "anytime"
    assert normalize_posted_within("24h") == "24h"


def test_fetch_window_is_constant():
    assert posted_within_to_days("24h") == max_job_fetch_days()
    assert posted_within_to_days("3d") == max_job_fetch_days()
    assert posted_within_to_days("anytime") == max_job_fetch_days()


def test_job_within_recency_24h():
    now = datetime(2026, 6, 27, 12, 0, tzinfo=timezone.utc)
    recent = (now - timedelta(hours=12)).isoformat().replace("+00:00", "Z")
    old = (now - timedelta(days=5)).isoformat().replace("+00:00", "Z")

    assert job_within_recency(_job(recent), "24h", now=now) is True
    assert job_within_recency(_job(old), "24h", now=now) is False
    assert job_within_recency(_job(""), "24h", now=now) is False  # undated excluded


def test_recency_windows_are_nested():
    now = datetime(2026, 6, 27, 12, 0, tzinfo=timezone.utc)
    recent = (now - timedelta(hours=12)).isoformat().replace("+00:00", "Z")
    mid = (now - timedelta(days=2)).isoformat().replace("+00:00", "Z")
    old = (now - timedelta(days=10)).isoformat().replace("+00:00", "Z")

    jobs = [_job(recent, "a"), _job(mid, "b"), _job(old, "c"), _job("", "d")]

    within_24h = {j.id for j in filter_jobs_by_recency(jobs, "24h", now=now)}
    within_3d = {j.id for j in filter_jobs_by_recency(jobs, "3d", now=now)}
    within_7d = {j.id for j in filter_jobs_by_recency(jobs, "7d", now=now)}
    within_any = {j.id for j in filter_jobs_by_recency(jobs, "anytime", now=now)}

    assert within_24h == {"a"}
    assert within_24h.issubset(within_3d)
    assert within_3d == {"a", "b"}
    assert within_3d.issubset(within_7d)
    assert within_7d == {"a", "b"}
    assert within_any == {"a", "b", "c", "d"}


def test_filter_jobs_by_recency():
    now = datetime(2026, 6, 27, 12, 0, tzinfo=timezone.utc)
    recent = (now - timedelta(days=1)).isoformat().replace("+00:00", "Z")
    old = (now - timedelta(days=10)).isoformat().replace("+00:00", "Z")
    jobs = [_job(recent), _job(old)]

    filtered = filter_jobs_by_recency(jobs, "7d", now=now)
    assert len(filtered) == 1
    assert filtered[0].published_at == recent

    assert len(filter_jobs_by_recency(jobs, "anytime", now=now)) == 2


def test_sort_jobs_for_display_newest_first():
    older = _job("2026-06-20T10:00:00Z", "old")
    newer = _job("2026-06-26T10:00:00Z", "new")
    undated = _job("", "unknown")
    sorted_jobs = sort_jobs_for_display([older, undated, newer])
    assert [j.id for j in sorted_jobs] == ["new", "old", "unknown"]
