"""Location profiles with researched job platforms and matching rules."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LocationProfile:
    """Regional job discovery profile — sources are fetch adapter IDs, not marketing names."""
    key: str
    aliases: frozenset[str]
    city_markers: tuple[str, ...]
    foreign_markers: tuple[str, ...]
    fetch_sources: tuple[str, ...]
    researched_platforms: tuple[str, ...]


def _norm(text: str) -> str:
    return " ".join((text or "").lower().split())


# Researched 2025–2026: Naukri (volume/recruiter reach), LinkedIn (MNC/startups),
# Indeed India (aggregator breadth). Shine.com added as fetchable India-native board
# when Naukri/Indeed block automated access (captchas / bot protection).
INDIA = LocationProfile(
    key="india",
    aliases=frozenset({"india", "indian", "bharat", "hindustan"}),
    city_markers=(
        "bangalore", "bengaluru", "mumbai", "bombay", "delhi", "new delhi",
        "ncr", "gurugram", "gurgaon", "noida", "hyderabad", "secunderabad",
        "chennai", "madras", "pune", "kolkata", "calcutta", "ahmedabad",
        "jaipur", "kochi", "cochin", "indore", "chandigarh", "lucknow",
        "nagpur", "visakhapatnam", "vizag", "bhubaneswar", "coimbatore",
    ),
    foreign_markers=(
        "united states", "usa", " u.s.", "canada", "united kingdom", " uk",
        "europe", "emea", "apac", "australia", "germany", "france",
    ),
    fetch_sources=("linkedin", "naukri", "indeed_india"),
    researched_platforms=("Naukri.com", "LinkedIn India", "Indeed India"),
)

US = LocationProfile(
    key="us",
    aliases=frozenset({
        "united states", "usa", "us", "u.s.", "u.s", "america",
        "united states of america",
    }),
    city_markers=(),  # handled by dedicated US logic
    foreign_markers=(
        "emea", "apac", "latam", "mena", "europe", "european union", " eu ",
        "united kingdom", " uk", "england", "scotland", "wales", "ireland",
        "germany", "france", "netherlands", "amsterdam", "spain", "italy",
        "canada", "toronto", "vancouver", "montreal", "mexico", "brazil",
        "australia", "sydney", "melbourne", "new zealand", "singapore",
        "india", "bangalore", "mumbai", "japan", "tokyo", "china", "korea",
        "israel", "dubai", "uae", "london", "paris", "berlin",
    ),
    fetch_sources=("linkedin", "greenhouse", "hiringcafe"),
    researched_platforms=("LinkedIn", "Greenhouse", "Hiring Cafe"),
)

UK = LocationProfile(
    key="uk",
    aliases=frozenset({"united kingdom", "uk", "u.k.", "britain", "great britain"}),
    city_markers=(
        "london", "manchester", "birmingham", "leeds", "glasgow", "edinburgh",
        "bristol", "liverpool", "cambridge", "oxford", "belfast",
    ),
    foreign_markers=("united states", "usa", "india", "emea", "europe"),
    fetch_sources=("linkedin", "hiringcafe", "greenhouse"),
    researched_platforms=("LinkedIn UK", "Indeed UK", "Reed.co.uk"),
)

DEFAULT = LocationProfile(
    key="global",
    aliases=frozenset(),
    city_markers=(),
    foreign_markers=(),
    fetch_sources=("linkedin", "hiringcafe", "greenhouse"),
    researched_platforms=("LinkedIn", "Hiring Cafe", "Greenhouse"),
)

_PROFILES: tuple[LocationProfile, ...] = (INDIA, US, UK)


def match_location_profile(location: str) -> LocationProfile:
    text = _norm(location)
    if not text:
        return DEFAULT
    for profile in _PROFILES:
        if text in profile.aliases:
            return profile
        if any(alias in text for alias in profile.aliases):
            return profile
        if any(city in text for city in profile.city_markers):
            return profile
    return DEFAULT


def resolve_fetch_sources(location: str, preferred: list[str] | None = None) -> list[str]:
    """Pick fetch adapters for a location, intersecting with user preference when set."""
    from services.guardrails.input import filter_job_sources

    regional = list(match_location_profile(location).fetch_sources)
    if not preferred:
        return filter_job_sources(regional)
    allowed = set(filter_job_sources(preferred))
    picked = [s for s in regional if s in allowed]
    return picked or filter_job_sources(regional)
