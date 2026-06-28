"""Aggregate real job listings from location-aware job platforms."""
import asyncio

import httpx

from config import settings
from models.schemas import JobListing
from services.job_sanitize import sanitize_job_listing
from services.job_recency import max_job_fetch_days, sort_jobs_for_display
from services.location_filter import job_matches_location
from services.location_registry import match_location_profile, resolve_fetch_sources
from services.sources.greenhouse_source import fetch_greenhouse_jobs
from services.sources.hiringcafe_source import fetch_hiringcafe_jobs
from services.sources.indeed_india_source import fetch_indeed_india_jobs
from services.sources.linkedin_source import fetch_linkedin_jobs
from services.sources.naukri_source import fetch_naukri_jobs
from services.sources.shine_source import fetch_shine_jobs

USER_AGENT = "AI-Career-Copilot/1.0"
TIMEOUT = 18.0

# All supported fetch adapters
SOURCES = (
    "linkedin", "greenhouse", "hiringcafe", "shine", "naukri", "indeed_india",
)


async def fetch_job_feed(
    search: str = "",
    sources: list[str] | None = None,
    limit_per_source: int = 15,
    remote_only: bool = False,
    location: str = "",
    posted_within: str = "anytime",  # noqa: ARG001 — recency applied at serve time
) -> tuple[list[JobListing], list[str]]:
    """
    Fetch jobs from upstream sources using the widest configured window.
    Source list is resolved from location when not explicitly provided.
    """
    loc = location or settings.linkedin_default_location
    active = resolve_fetch_sources(loc, sources)
    # Shine.com provides live India listings when Naukri/Indeed block automated fetch.
    if match_location_profile(loc).key == "india" and "shine" not in active:
        active = [*active, "shine"]
    if not active:
        active = list(SOURCES)[:3]

    fetch_days = max_job_fetch_days()
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json, text/html"}
    async with httpx.AsyncClient(timeout=TIMEOUT, headers=headers, follow_redirects=True) as client:
        tasks = []
        source_names: list[str] = []
        for name in active:
            if name == "linkedin":
                tasks.append(fetch_linkedin_jobs(client, search, loc, limit_per_source))
                source_names.append(name)
            elif name == "greenhouse":
                tasks.append(
                    fetch_greenhouse_jobs(client, settings.greenhouse_boards, search, limit_per_source)
                )
                source_names.append(name)
            elif name == "hiringcafe":
                tasks.append(
                    fetch_hiringcafe_jobs(
                        client, search, limit_per_source, loc, days=fetch_days,
                    )
                )
                source_names.append(name)
            elif name == "shine":
                tasks.append(fetch_shine_jobs(client, search, loc, limit_per_source))
                source_names.append(name)
            elif name == "naukri":
                tasks.append(fetch_naukri_jobs(client, search, loc, limit_per_source))
                source_names.append(name)
            elif name == "indeed_india":
                tasks.append(fetch_indeed_india_jobs(client, search, loc, limit_per_source))
                source_names.append(name)
        results = await asyncio.gather(*tasks, return_exceptions=True)

    merged: list[JobListing] = []
    used_sources: list[str] = []
    seen_keys: set[str] = set()

    for name, result in zip(source_names, results):
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
