"""Tests for India location filtering and regional source resolution."""
from models.schemas import JobListing
from services.location_registry import match_location_profile, resolve_fetch_sources
from services.location_filter import job_matches_location


def _job(**kwargs) -> JobListing:
    base = dict(
        id="shine:1",
        title="Software Engineer",
        company="Acme",
        apply_url="https://example.com/apply",
        source="shine",
    )
    base.update(kwargs)
    return JobListing(**base)


def test_india_profile_from_bengaluru():
    profile = match_location_profile("Bengaluru, India")
    assert profile.key == "india"


def test_india_sources_are_top_platforms():
    sources = resolve_fetch_sources("India")
    assert sources == ["linkedin", "naukri", "indeed_india"]


def test_india_filter_includes_bangalore_without_india_word():
    job = _job(location="Bangalore, Karnataka", source="shine")
    assert job_matches_location(job, "India") is True


def test_india_filter_excludes_us_only():
    job = _job(
        location="San Francisco, CA",
        source="greenhouse",
        title="Software Engineer",
    )
    assert job_matches_location(job, "India") is False


def test_india_filter_keeps_regional_sources():
    job = _job(location="Remote", source="naukri", title="Backend Developer")
    assert job_matches_location(job, "India") is True


def test_us_still_excludes_netherlands():
    job = _job(
        id="greenhouse:databricks:1",
        location="Amsterdam, Netherlands",
        source="greenhouse",
        title="Engineer",
    )
    assert job_matches_location(job, "United States") is False
