"""Tests for job posted-date normalization."""
from datetime import datetime, timezone

from services.job_dates import normalize_published_at, parse_published_at


def test_normalize_iso_z():
    assert normalize_published_at("2026-06-27T10:00:00Z") == "2026-06-27T10:00:00Z"


def test_normalize_epoch_milliseconds():
    dt = datetime(2026, 6, 27, 10, 0, tzinfo=timezone.utc)
    ms = int(dt.timestamp() * 1000)
    assert normalize_published_at(str(ms)) == "2026-06-27T10:00:00Z"


def test_parse_relative_hours():
    ref = datetime(2026, 6, 27, 12, 0, tzinfo=timezone.utc)
    parsed = parse_published_at("6 hours ago", reference=ref)
    assert parsed is not None
    assert parsed.hour == 6


def test_parse_relative_days():
    ref = datetime(2026, 6, 27, 12, 0, tzinfo=timezone.utc)
    parsed = parse_published_at("2 days ago", reference=ref)
    assert parsed is not None
    assert parsed.day == 25


def test_normalize_invalid_returns_empty():
    assert normalize_published_at("") == ""
    assert normalize_published_at("not-a-date") == ""
