"""Regression test for job feed location filter import."""

from unittest.mock import AsyncMock, patch

from models.schemas import JobListing
from services.job_feed_service import fetch_job_feed


@patch("services.job_feed_service.fetch_linkedin_jobs", new_callable=AsyncMock)
async def test_fetch_job_feed_applies_location_filter(mock_linkedin):
    mock_linkedin.return_value = [
        JobListing(
            id="li:1",
            title="Engineer",
            company="Acme",
            description="Build systems",
            location="San Francisco, CA",
            apply_url="https://example.com/1",
            source="linkedin",
        ),
        JobListing(
            id="li:2",
            title="Engineer",
            company="RemoteCo",
            description="Remote role",
            location="Remote",
            remote=True,
            apply_url="https://example.com/2",
            source="linkedin",
        ),
    ]

    jobs, sources = await fetch_job_feed(
        search="engineer",
        sources=["linkedin"],
        limit_per_source=5,
        location="United States",
    )

    assert sources == ["linkedin"]
    assert len(jobs) >= 1
    assert all(job.apply_url for job in jobs)
