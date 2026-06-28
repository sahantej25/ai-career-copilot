"""Indeed India (in.indeed.com) — aggregator; portal fallback when bot protection blocks fetch."""
from urllib.parse import quote_plus

import httpx

from models.schemas import JobListing

INDEED_BASE = "https://in.indeed.com/jobs"
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml",
}


def indeed_india_search_url(search: str, location: str = "India") -> str:
    q = quote_plus(search.strip() or "software engineer")
    loc = quote_plus(location.strip() or "India")
    return f"{INDEED_BASE}?q={q}&l={loc}&sort=date"


async def fetch_indeed_india_jobs(
    client: httpx.AsyncClient,
    search: str,
    location: str,
    limit: int,
) -> list[JobListing]:
    keyword = search.strip() or "software engineer"
    loc = location.strip() or "India"
    jobs: list[JobListing] = []

    # Indeed India blocks most automated fetches (403). Provide a deep-link portal card.
    jobs.append(
        JobListing(
            id="indeed_india:search-portal",
            title=f'Browse "{keyword}" on Indeed India',
            company="Indeed India",
            location=loc,
            remote=False,
            description=(
                "Indeed India aggregates listings from company career pages, Naukri, LinkedIn, "
                "and other boards. Open Indeed India to browse fresh postings, then track "
                "applications in your pipeline."
            ),
            excerpt="India job aggregator — opens in.indeed.com with your search.",
            tags=["India", "Indeed", "Aggregator"],
            apply_url=indeed_india_search_url(keyword, loc),
            source="indeed_india",
        )
    )
    return jobs[:limit]
