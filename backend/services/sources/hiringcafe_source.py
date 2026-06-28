"""Hiring Cafe job discovery — API attempt with search-page fallback."""
import json
import re
from urllib.parse import quote_plus

import httpx

from models.schemas import JobListing
from services.job_dates import normalize_published_at
from services.job_match_scorer import job_excerpt, strip_html

HC_SEARCH_API = "https://hiring.cafe/api/search-jobs"
HC_SITE = "https://hiring.cafe"
BROWSER_HEADERS = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "content-type": "application/json",
    "origin": HC_SITE,
    "referer": f"{HC_SITE}/",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
    ),
}


def _default_search_state(search: str, location: str = "", days: int = 14) -> dict:
    locations: list[dict] = []
    loc = (location or "").strip()
    if loc:
        locations = [{"formatted_address": loc, "name": loc}]
    return {
        "jobTitleQuery": search.strip(),
        "searchQuery": search.strip(),
        "dateFetchedPastNDays": max(1, min(days, 30)),
        "workplaceTypes": ["Remote", "Hybrid", "Onsite"],
        "seniorityLevel": ["No Prior Experience Required", "Entry Level", "Mid Level", "Senior Level"],
        "commitmentTypes": ["Full Time", "Part Time", "Contract", "Internship"],
        "locations": locations,
        "sortBy": "default",
    }


def _parse_hiringcafe_jobs(payload: dict, limit: int) -> list[JobListing]:
    """Normalize Hiring Cafe API / embedded JSON shapes."""
    jobs: list[JobListing] = []
    candidates = (
        payload.get("jobs")
        or payload.get("results")
        or payload.get("data", {}).get("jobs")
        or payload.get("props", {}).get("pageProps", {}).get("jobs")
        or []
    )
    if not isinstance(candidates, list):
        return []

    for item in candidates[:limit]:
        if not isinstance(item, dict):
            continue
        title = item.get("jobTitle") or item.get("title") or "Untitled Role"
        company = item.get("companyName") or item.get("company") or "Unknown Company"
        desc = item.get("jobDescription") or item.get("description") or item.get("excerpt") or ""
        apply = (
            item.get("applyUrl")
            or item.get("apply_url")
            or item.get("url")
            or item.get("jobUrl")
            or ""
        )
        job_id = item.get("id") or item.get("_id") or item.get("slug") or title
        location = item.get("location") or item.get("jobGeo") or ""
        if isinstance(location, dict):
            location = location.get("formatted_address") or location.get("name") or ""

        jobs.append(
            JobListing(
                id=f"hiringcafe:{job_id}",
                title=str(title),
                company=str(company),
                location=str(location),
                remote=bool(item.get("remote") or "remote" in str(location).lower()),
                job_type=str(item.get("commitmentType") or item.get("jobType") or ""),
                salary=str(item.get("salary") or item.get("compensation") or ""),
                description=str(desc),
                excerpt=job_excerpt(str(desc)),
                tags=[str(t) for t in (item.get("tags") or item.get("skills") or [])[:8] if t],
                apply_url=str(apply) if apply else hiringcafe_search_url(str(title)),
                source="hiringcafe",
                company_logo=str(item.get("companyLogo") or ""),
                published_at=normalize_published_at(
                    item.get("postedAt") or item.get("pubDate") or item.get("datePosted")
                ),
            )
        )
    return jobs


def hiringcafe_search_url(search: str) -> str:
    q = quote_plus(search.strip() or "software engineer")
    return f"{HC_SITE}/?q={q}"


async def _try_api(client: httpx.AsyncClient, search: str, limit: int, location: str = "", days: int = 14) -> list[JobListing]:
    body = {"size": min(limit, 40), "page": 0, "searchState": _default_search_state(search, location, days)}
    resp = await client.post(HC_SEARCH_API, json=body, headers=BROWSER_HEADERS)
    if resp.status_code != 200:
        return []
    try:
        data = resp.json()
    except json.JSONDecodeError:
        return []
    if isinstance(data, dict) and data.get("error"):
        return []
    return _parse_hiringcafe_jobs(data if isinstance(data, dict) else {}, limit)


async def _try_next_data(client: httpx.AsyncClient, search: str, limit: int) -> list[JobListing]:
    url = hiringcafe_search_url(search)
    resp = await client.get(url, headers={**BROWSER_HEADERS, "accept": "text/html"})
    if resp.status_code != 200:
        return []
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', resp.text)
    if not match:
        return []
    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError:
        return []
    return _parse_hiringcafe_jobs(payload, limit)


async def fetch_hiringcafe_jobs(
    client: httpx.AsyncClient,
    search: str,
    limit: int,
    location: str = "",
    days: int = 14,
) -> list[JobListing]:
    jobs = await _try_api(client, search, limit, location, days)
    if jobs:
        return jobs
    jobs = await _try_next_data(client, search, limit)
    if jobs:
        return jobs

    # Graceful fallback: deep-link search on Hiring Cafe (user applies there)
    keyword = search.strip() or "software engineer"
    return [
        JobListing(
            id="hiringcafe:search-portal",
            title=f"Browse \"{keyword}\" on Hiring Cafe",
            company="Hiring Cafe",
            location="Multi-source aggregator",
            remote=True,
            description=(
                "Hiring Cafe aggregates real postings from LinkedIn, Greenhouse, Lever, Ashby, "
                "and company career pages. Open the portal to browse live listings, then track "
                "applications here using Add External Job or Tailor & Apply."
            ),
            excerpt="Live aggregator — opens hiring.cafe with your search.",
            tags=["Aggregator", "Multi-board"],
            apply_url=hiringcafe_search_url(keyword),
            source="hiringcafe",
            published_at="",
        )
    ]
