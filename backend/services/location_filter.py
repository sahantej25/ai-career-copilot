"""Location matching for aggregated job feeds."""
import re

from models.schemas import JobListing
from services.location_registry import US, match_location_profile

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

US_MARKERS = (
    "united states", "united states of america", "usa", "u.s.a", "u.s.",
    " us,", " us)", " us ", " us-", "remote - us", "remote (us)", "remote, us",
    "remote us", "us remote", "us-based", "us based", "north america",
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


def _has_markers(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)


def _has_alias(text: str, aliases: frozenset[str]) -> bool:
    return any(re.search(rf"\b{re.escape(alias)}\b", text) for alias in aliases)


def _job_text_blob(job: JobListing) -> str:
    return _normalize(f"{job.location} {job.title} {job.excerpt} {job.description}")


def job_matches_location(job: JobListing, filter_location: str) -> bool:
    """Return True when a job should appear for the user's location filter."""
    fl = _normalize(filter_location)
    if not fl:
        return True

    profile = match_location_profile(filter_location)
    combined = _job_text_blob(job)

    if profile.key == "us" or fl in US.aliases:
        if _has_markers(combined, US.foreign_markers) and not _has_us_marker(combined):
            return False
        if _has_us_marker(combined):
            return True
        if job.remote and _normalize(job.location) in {"", "remote", "see posting", "multiple locations"}:
            return False
        return False

    if profile.key == "india":
        if _has_markers(combined, profile.foreign_markers) and not (
            _has_markers(combined, profile.city_markers)
            or "india" in combined
            or _has_alias(combined, profile.aliases)
        ):
            return False
        if (
            _has_markers(combined, profile.city_markers)
            or "india" in combined
            or _has_alias(combined, profile.aliases)
        ):
            return True
        # India-targeted fetch adapters may return broader listings — keep if source is regional.
        if job.source in {"shine", "naukri", "indeed_india"}:
            return True
        return False

    if profile.city_markers:
        if any(city in combined for city in profile.city_markers):
            return True
        if fl in combined:
            return True
        return False

    return fl in combined or fl in _normalize(job.location)
