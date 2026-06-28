"""Location matching for aggregated job feeds."""
import re

from models.schemas import JobListing

US_FILTER_ALIASES = frozenset(
    {"united states", "usa", "us", "u.s.", "u.s", "america", "united states of america"}
)

US_MARKERS = (
    "united states",
    "united states of america",
    "usa",
    "u.s.a",
    "u.s.",
    " us,",
    " us)",
    " us ",
    " us-",
    "remote - us",
    "remote (us)",
    "remote, us",
    "remote us",
    "us remote",
    "us-based",
    "us based",
    "north america",
)

US_STATE_NAMES = (
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho",
    "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana",
    "maine", "maryland", "massachusetts", "michigan", "minnesota",
    "mississippi", "missouri", "montana", "nebraska", "nevada",
    "new hampshire", "new jersey", "new mexico", "new york", "north carolina",
    "north dakota", "ohio", "oklahoma", "oregon", "pennsylvania",
    "rhode island", "south carolina", "south dakota", "tennessee", "texas",
    "utah", "vermont", "virginia", "washington", "west virginia",
    "wisconsin", "wyoming", "district of columbia",
)

US_STATE_ABBREVS = frozenset(
    "AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO "
    "MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI DC".split()
)

NON_US_MARKERS = (
    "emea", "apac", "latam", "mena", "europe", "european union", " eu ",
    "united kingdom", " uk", "england", "scotland", "wales", "ireland",
    "germany", "france", "netherlands", "amsterdam", "spain", "italy",
    "poland", "sweden", "norway", "denmark", "finland", "belgium",
    "switzerland", "austria", "portugal", "czech", "romania", "hungary",
    "canada", "toronto", "vancouver", "montreal", "mexico", "brazil",
    "argentina", "australia", "sydney", "melbourne", "new zealand",
    "singapore", "india", "bangalore", "mumbai", "japan", "tokyo",
    "china", "beijing", "shanghai", "korea", "seoul", "israel", "tel aviv",
    "dubai", "uae", "south africa", "nigeria", "philippines", "vietnam",
    "thailand", "indonesia", "malaysia", "taiwan", "hong kong",
    "london", "paris", "berlin", "munich", "dublin", "zurich", "geneva",
)

_STATE_ABBREV_RE = re.compile(
    r",\s*(" + "|".join(sorted(US_STATE_ABBREVS, key=len, reverse=True)) + r")\b",
    re.I,
)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def _has_us_marker(text: str) -> bool:
    if not text:
        return False
    if any(marker in text for marker in US_MARKERS):
        return True
    if any(f", {name}" in text or text.endswith(name) for name in US_STATE_NAMES):
        return True
    if _STATE_ABBREV_RE.search(text):
        return True
    return False


def _has_non_us_marker(text: str) -> bool:
    return any(marker in text for marker in NON_US_MARKERS)


def job_matches_location(job: JobListing, filter_location: str) -> bool:
    """Return True when a job should appear for the user's location filter."""
    fl = _normalize(filter_location)
    if not fl:
        return True

    loc = _normalize(job.location)
    title = _normalize(job.title)
    excerpt = _normalize(job.excerpt)
    combined = f"{loc} {title} {excerpt}"

    if fl in US_FILTER_ALIASES:
        if _has_non_us_marker(combined) and not _has_us_marker(combined):
            return False
        if _has_us_marker(combined):
            return True
        # Ambiguous remote/global listings without a US anchor are excluded.
        if job.remote and loc in {"", "remote", "see posting", "multiple locations"}:
            return False
        return False

    # Generic substring match for city/country-specific filters.
    return fl in loc or fl in title or fl in excerpt
