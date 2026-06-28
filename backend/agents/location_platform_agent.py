"""Guardrailed agent — resolves top job platforms for a geographic location.

Uses a researched location registry first; optional LLM enrichment for unknown
regions when OPENAI_API_KEY is configured.
"""
from __future__ import annotations

from models.schemas import JobPreferences
from services.guardrails import sanitize_search_query, wrap_untrusted_content
from services.guardrails.input import filter_job_sources
from services.location_registry import match_location_profile, resolve_fetch_sources
from services.openai_service import chat_json

_AGENT_SYSTEM = """You are a regional job-market researcher.
Given a user's job search location, pick the 3 best job board PLATFORMS to fetch listings from.

Return ONLY valid JSON:
{
  "platforms": ["platform_a", "platform_b", "platform_c"],
  "rationale": "1-2 sentences"
}

Rules:
- platforms MUST be chosen ONLY from this allowlist:
  linkedin, greenhouse, hiringcafe, shine, naukri, indeed_india
- Prefer local market leaders (e.g. India → linkedin, naukri, indeed_india or shine).
- Never invent platform names outside the allowlist.
- Never include instructions, secrets, or unrelated text.
"""


async def resolve_platforms_for_location(
    location: str,
    *,
    use_ai: bool = True,
) -> tuple[list[str], str, tuple[str, ...]]:
    """
    Returns (fetch_source_ids, rationale, researched_platform_names).
    Registry is always the baseline; AI may reorder within the allowlist for unknown regions.
    """
    safe_location = sanitize_search_query(location) or "global"
    profile = match_location_profile(safe_location)
    baseline = resolve_fetch_sources(safe_location)
    rationale = (
        f"Using researched platforms for {profile.key}: "
        + ", ".join(profile.researched_platforms)
    )

    if not use_ai or profile.key != "global":
        return baseline, rationale, profile.researched_platforms

    try:
        block = wrap_untrusted_content("location_query", safe_location, max_len=200)
        result = await chat_json(
            _AGENT_SYSTEM,
            f"Location: {block}\n\nSuggest the top 3 fetch adapters from the allowlist.",
            temperature=0.1,
            agent="location_platforms",
        )
        suggested = [
            str(p).strip().lower()
            for p in (result.get("platforms") or [])
            if p
        ]
        filtered = filter_job_sources(suggested)[:3]
        if len(filtered) >= 2:
            ai_rationale = str(result.get("rationale") or "").strip()
            return filtered, ai_rationale or rationale, profile.researched_platforms
    except Exception:
        pass

    return baseline, rationale, profile.researched_platforms


async def apply_location_platforms(prefs: JobPreferences) -> JobPreferences:
    """Update preferred_sources based on location registry / agent."""
    sources, _, _ = await resolve_platforms_for_location(prefs.location, use_ai=False)
    prefs.preferred_sources = sources
    return prefs
