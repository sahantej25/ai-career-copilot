"""LinkedIn public guest job search (seeMoreJobPostings)."""
import re
from urllib.parse import quote_plus

import httpx

from models.schemas import JobListing
from services.job_dates import normalize_published_at

LINKEDIN_SEARCH = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

_CARD_MARKER = re.compile(r'data-entity-urn="urn:li:jobPosting:(\d+)"')


def _clean_title(raw: str) -> str:
    return re.sub(r"\s+", " ", raw).strip()


def _extract_published_at(card_html: str) -> str:
    time_match = re.search(r'<time[^>]+datetime="([^"]+)"', card_html, re.I)
    if time_match:
        return normalize_published_at(time_match.group(1))

    listdate = re.search(
        r'class="job-search-card__listdate[^"]*"[^>]*>\s*([^<]+?)\s*<',
        card_html,
        re.I,
    )
    if listdate:
        return normalize_published_at(listdate.group(1))

    footer = re.search(
        r'class="job-search-card__footer-item[^"]*"[^>]*>\s*([^<]+?)\s*<',
        card_html,
        re.I,
    )
    if footer:
        return normalize_published_at(footer.group(1))

    return ""


def _parse_linkedin_html(html: str) -> list[dict]:
    rows: list[dict] = []
    markers = list(_CARD_MARKER.finditer(html))
    for idx, match in enumerate(markers):
        job_id = match.group(1)
        start = match.start()
        end = markers[idx + 1].start() if idx + 1 < len(markers) else len(html)
        card = html[start:end]

        title_match = re.search(r'class="sr-only">\s*([^<]+?)\s*</span>', card)
        link_match = re.search(r'href="(https://www.linkedin.com/jobs/view/[^"]+)"', card)
        company_match = re.search(r'class="hidden-nested-link">([^<]+)</a>', card)
        location_match = re.search(r'class="job-search-card__location">([^<]+)</span>', card)

        if not title_match or not link_match:
            continue

        url = link_match.group(1).split("?")[0]
        rows.append({
            "id": job_id,
            "title": _clean_title(title_match.group(1)),
            "url": url,
            "company": company_match.group(1).strip() if company_match else "",
            "location": location_match.group(1).strip() if location_match else "",
            "published_at": _extract_published_at(card),
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
                    published_at=row.get("published_at") or "",
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
