"""Shine.com — India job board with a public search API."""
from urllib.parse import quote_plus

import httpx

from models.schemas import JobListing
from services.job_dates import normalize_published_at
from services.job_match_scorer import job_excerpt, strip_html

SHINE_API = "https://www.shine.com/api/v2/search/simple/"
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


def shine_search_url(search: str, location: str = "India") -> str:
    q = quote_plus(search.strip() or "software engineer")
    loc = quote_plus(location.strip() or "India")
    return f"https://www.shine.com/jobs/{q}-jobs-in-{loc.replace('+', '-')}"


def _format_location(raw: object) -> str:
    if isinstance(raw, list):
        parts = [str(x).strip() for x in raw if x]
        return ", ".join(parts[:4])
    return str(raw or "").strip()


async def fetch_shine_jobs(
    client: httpx.AsyncClient,
    search: str,
    location: str,
    limit: int,
) -> list[JobListing]:
    keyword = search.strip() or "software engineer"
    loc = location.strip() or "India"
    jobs: list[JobListing] = []

    page = 1
    while len(jobs) < limit and page <= 3:
        resp = await client.get(
            SHINE_API,
            params={"q": keyword, "loc": loc, "page": page},
            headers=BROWSER_HEADERS,
        )
        if resp.status_code != 200:
            break
        try:
            payload = resp.json()
        except Exception:
            break
        rows = payload.get("results") or []
        if not rows:
            break
        for item in rows:
            if not isinstance(item, dict):
                continue
            title = str(item.get("jJT") or "Untitled Role")
            company = str(item.get("jCName") or "Company on Shine")
            slug = str(item.get("jSlug") or "")
            job_id = str(item.get("id") or slug or title)
            loc_str = _format_location(item.get("jLoc"))
            desc = strip_html(str(item.get("jJD") or item.get("jJDT") or ""))
            tags = [
                t.strip()
                for t in str(item.get("jKwd") or "").split(",")
                if t.strip()
            ][:8]
            apply_url = f"https://www.shine.com/jobs/{slug}" if slug else shine_search_url(keyword, loc)
            jobs.append(
                JobListing(
                    id=f"shine:{job_id}",
                    title=title,
                    company=company,
                    location=loc_str or loc,
                    remote="remote" in title.lower() or "remote" in loc_str.lower(),
                    job_type="",
                    salary="",
                    description=desc or f"{title} at {company}",
                    excerpt=job_excerpt(desc or title),
                    tags=tags,
                    apply_url=apply_url,
                    source="shine",
                    company_logo="",
                    published_at=normalize_published_at(item.get("jPDate")),
                )
            )
            if len(jobs) >= limit:
                break
        page += 1

    return jobs
