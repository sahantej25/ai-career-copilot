"""Naukri.com — India's largest job portal (API requires captcha; portal + best-effort)."""
from urllib.parse import quote_plus

import httpx

from models.schemas import JobListing

NAUKRI_API = "https://www.naukri.com/jobapi/v3/search"
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
    ),
    "Accept": "application/json",
    "appid": "135",
    "systemid": "135",
}


def naukri_search_url(search: str, location: str = "India") -> str:
    q = quote_plus(search.strip() or "software engineer")
    loc = quote_plus(location.strip() or "India")
    return f"https://www.naukri.com/{q.replace('+', '-')}-jobs-in-{loc.replace('+', '-')}"


async def fetch_naukri_jobs(
    client: httpx.AsyncClient,
    search: str,
    location: str,
    limit: int,
) -> list[JobListing]:
    keyword = search.strip() or "software engineer"
    loc = location.strip() or "India"
    jobs: list[JobListing] = []

    try:
        resp = await client.get(
            NAUKRI_API,
            params={
                "noOfResults": min(limit, 20),
                "keyword": keyword,
                "location": loc,
            },
            headers=BROWSER_HEADERS,
        )
        if resp.status_code == 200:
            payload = resp.json()
            rows = payload.get("jobDetails") or payload.get("jobs") or []
            for item in rows[:limit]:
                if not isinstance(item, dict):
                    continue
                title = str(item.get("title") or item.get("designation") or "Role on Naukri")
                company = str(item.get("companyName") or item.get("company") or "Company on Naukri")
                job_id = str(item.get("jobId") or item.get("id") or title)
                place = str(item.get("placeholders") or item.get("location") or loc)
                apply_url = str(item.get("applyUrl") or item.get("jdURL") or naukri_search_url(keyword, loc))
                jobs.append(
                    JobListing(
                        id=f"naukri:{job_id}",
                        title=title,
                        company=company,
                        location=place,
                        remote="remote" in title.lower() or "remote" in place.lower(),
                        description=f"{title} at {company}. View on Naukri.com.",
                        excerpt=f"{title} · {company} · {place}",
                        tags=[],
                        apply_url=apply_url,
                        source="naukri",
                        published_at=str(item.get("createdDate") or item.get("postedOn") or ""),
                    )
                )
    except Exception:
        pass

    if not jobs:
        jobs.append(
            JobListing(
                id="naukri:search-portal",
                title=f'Browse "{keyword}" on Naukri.com',
                company="Naukri.com",
                location=loc,
                remote=False,
                description=(
                    "Naukri is India's largest job portal with 70M+ registered job seekers. "
                    "Live listings require browser access — open Naukri to browse and apply, "
                    "then track applications here."
                ),
                excerpt="India's #1 job board — opens naukri.com with your search.",
                tags=["India", "Naukri", "Portal"],
                apply_url=naukri_search_url(keyword, loc),
                source="naukri",
            )
        )
    return jobs[:limit]
