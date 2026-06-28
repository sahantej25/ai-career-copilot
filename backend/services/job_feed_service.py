"""Aggregate real job listings from LinkedIn, Greenhouse, and Hiring Cafe."""
import asyncio

import httpx

from config import settings
from models.schemas import JobListing
from services.job_sanitize import sanitize_job_listing
from services.job_recency import max_job_fetch_days, sort_jobs_for_display
from services.location_filter import job_matches_location
from services.sources.greenhouse_source import fetch_greenhouse_jobs
from services.sources.hiringcafe_source import fetch_hiringcafe_jobs
from services.sources.linkedin_source import fetch_linkedin_jobs

USER_AGENT = "AI-Career-Copilot/1.0"
TIMEOUT = 18.0

# Primary sources requested by product
SOURCES = ("linkedin", "greenhouse", "hiringcafe")


async def fetch_job_feed(
    search: str = "",
    sources: list[str] | None = None,
    limit_per_source: int = 15,
    remote_only: bool = False,
    location: str = "",
    posted_within: str = "anytime",  # noqa: ARG001 — recency applied at serve time, not fetch time
) -> tuple[list[JobListing], list[str]]:
    """
    Fetch jobs from upstream sources using the widest configured window.
    Recency filtering is applied later so 24h ⊆ 3d ⊆ 7d ⊆ anytime on the same cache.
    """
    active = [s for s in (sources or list(SOURCES)) if s in SOURCES]
    if not active:
        active = list(SOURCES)

    loc = location or settings.linkedin_default_location
    fetch_days = max_job_fetch_days()
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json, text/html"}
    async with httpx.AsyncClient(timeout=TIMEOUT, headers=headers, follow_redirects=True) as client:
        tasks = []
        for name in active:
            if name == "linkedin":
                tasks.append(fetch_linkedin_jobs(client, search, loc, limit_per_source))
            elif name == "greenhouse":
                tasks.append(
                    fetch_greenhouse_jobs(client, settings.greenhouse_boards, search, limit_per_source)
                )
            elif name == "hiringcafe":
                tasks.append(
                    fetch_hiringcafe_jobs(
                        client, search, limit_per_source, loc,
                        days=fetch_days,
                    )
                )
        results = await asyncio.gather(*tasks, return_exceptions=True)

    merged: list[JobListing] = []
    used_sources: list[str] = []
    seen_keys: set[str] = set()

    for name, result in zip(active, results):
        if isinstance(result, Exception):
            continue
        if not result:
            continue
        used_sources.append(name)
        for job in result:
            if remote_only and not job.remote:
                continue
            if not job_matches_location(job, loc):
                continue
            if not job.apply_url:
                continue
            dedupe_key = f"{job.source}|{job.company.lower()}|{job.title.lower()}"
            if dedupe_key in seen_keys:
                continue
            seen_keys.add(dedupe_key)
            merged.append(sanitize_job_listing(job))

    return sort_jobs_for_display(merged), used_sources
