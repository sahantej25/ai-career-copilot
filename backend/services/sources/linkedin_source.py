"""LinkedIn public guest job search (seeMoreJobPostings)."""
import re
from urllib.parse import quote_plus

import httpx

from models.schemas import JobListing
from services.job_match_scorer import strip_html

LINKEDIN_SEARCH = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _clean_title(raw: str) -> str:
    return re.sub(r"\s+", " ", raw).strip()


def _parse_linkedin_html(html: str) -> list[dict]:
    titles = [_clean_title(t) for t in re.findall(r'class="sr-only">\s*([^<]+?)\s*</span>', html)]
    links = re.findall(r'href="(https://www.linkedin.com/jobs/view/[^"]+)"', html)
    urns = re.findall(r'data-entity-urn="urn:li:jobPosting:(\d+)"', html)
    companies = [c.strip() for c in re.findall(r'class="hidden-nested-link">([^<]+)</a>', html)]
    locations = [loc.strip() for loc in re.findall(r'class="job-search-card__location">([^<]+)</span>', html)]

    rows: list[dict] = []
    count = min(len(urns), len(titles), len(links))
    for i in range(count):
        rows.append({
            "id": urns[i],
            "title": titles[i],
            "url": links[i].split("?")[0] if "?" in links[i] else links[i],
            "company": companies[i] if i < len(companies) else "",
            "location": locations[i] if i < len(locations) else "",
        })
    return rows


async def fetch_linkedin_jobs(
    client: httpx.AsyncClient,
    search: str,
    location: str,
    limit: int,
) -> list[JobListing]:
    jobs: list[JobListing] = []
    keywords = search.strip() or "software engineer"
    start = 0
    page_size = 25

    while len(jobs) < limit and start < 100:
        params = {
            "keywords": keywords,
            "location": location or "United States",
            "start": start,
        }
        resp = await client.get(LINKEDIN_SEARCH, params=params)
        if resp.status_code != 200:
            break
        rows = _parse_linkedin_html(resp.text)
        if not rows:
            break
        for row in rows:
            title = row["title"]
            company = row["company"] or "Company on LinkedIn"
            jobs.append(
                JobListing(
                    id=f"linkedin:{row['id']}",
                    title=title,
                    company=company,
                    location=row["location"] or location or "United States",
                    remote="remote" in title.lower() or "remote" in row["location"].lower(),
                    job_type="",
                    salary="",
                    description=f"{title} at {company}. View full details on LinkedIn.",
                    excerpt=f"{title} · {company} · {row['location'] or location}",
                    tags=_extract_tags(title),
                    apply_url=row["url"],
                    source="linkedin",
                    company_logo="",
                    published_at="",
                )
            )
            if len(jobs) >= limit:
                break
        start += page_size

    return jobs


def _extract_tags(title: str) -> list[str]:
    keywords = ["react", "python", "java", "node", "typescript", "aws", "frontend", "backend", "full stack", "data"]
    lower = title.lower()
    return [k.title() for k in keywords if k in lower]


def linkedin_search_url(search: str, location: str = "United States") -> str:
    q = quote_plus(search.strip() or "software engineer")
    loc = quote_plus(location or "United States")
    return f"https://www.linkedin.com/jobs/search/?keywords={q}&location={loc}"
