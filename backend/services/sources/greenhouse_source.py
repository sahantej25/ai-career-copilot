"""Greenhouse public Job Board API — real postings from company career pages."""
import asyncio

import httpx

from models.schemas import JobListing
from services.job_match_scorer import job_excerpt, strip_html

GH_API = "https://boards-api.greenhouse.io/v1/boards/{token}/jobs"


def _location_str(item: dict) -> str:
    loc = item.get("location") or {}
    if isinstance(loc, dict):
        return loc.get("name") or ""
    return str(loc) if loc else ""


async def _fetch_board(
    client: httpx.AsyncClient,
    token: str,
    search: str,
    limit: int,
) -> list[JobListing]:
    url = GH_API.format(token=token)
    resp = await client.get(url, params={"content": "true"})
    if resp.status_code != 200:
        return []

    data = resp.json()
    jobs: list[JobListing] = []
    search_lower = search.lower()

    for item in data.get("jobs", []):
        title = item.get("title") or "Untitled Role"
        desc = item.get("content") or ""
        blob = f"{title} {strip_html(desc)}".lower()
        if search_lower and search_lower not in blob:
            continue

        departments = item.get("departments") or []
        dept_names = [d.get("name", "") for d in departments if isinstance(d, dict)]
        location = _location_str(item)
        remote = "remote" in location.lower() or "remote" in title.lower()

        jobs.append(
            JobListing(
                id=f"greenhouse:{token}:{item.get('id')}",
                title=title,
                company=token.replace("-", " ").title(),
                location=location or "See posting",
                remote=remote,
                job_type="",
                salary="",
                description=desc,
                excerpt=job_excerpt(desc),
                tags=dept_names[:6],
                apply_url=item.get("absolute_url") or "",
                source="greenhouse",
                company_logo="",
                published_at=item.get("updated_at") or "",
            )
        )
        if len(jobs) >= limit:
            break
    return jobs


async def fetch_greenhouse_jobs(
    client: httpx.AsyncClient,
    boards: list[str],
    search: str,
    limit_per_board: int,
) -> list[JobListing]:
    if not boards:
        return []

    tasks = [_fetch_board(client, token, search, limit_per_board) for token in boards]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    merged: list[JobListing] = []
    for result in results:
        if isinstance(result, Exception):
            continue
        merged.extend(result)
    return merged
