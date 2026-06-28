"""Aggregate real job listings from LinkedIn, Greenhouse, and Hiring Cafe."""
import asyncio
from datetime import datetime

import httpx

from config import settings
from models.schemas import JobListing
from services.job_sanitize import sanitize_job_listing
from services.job_recency import filter_jobs_by_recency, posted_within_to_days
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
    posted_within: str = "anytime",
) -> tuple[list[JobListing], list[str]]:
    active = [s for s in (sources or list(SOURCES)) if s in SOURCES]
    if not active:
        active = list(SOURCES)

    loc = location or settings.linkedin_default_location
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
                        days=posted_within_to_days(posted_within),
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

    merged = filter_jobs_by_recency(merged, posted_within)

    def sort_key(job: JobListing):
        ts = job.published_at or ""
        try:
            if "T" in ts:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            else:
                dt = datetime.fromisoformat(ts)
            return dt.timestamp()
        except Exception:
            return 0.0

    merged.sort(key=sort_key, reverse=True)
    return merged, used_sources
