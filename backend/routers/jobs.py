from fastapi import APIRouter, Depends, Query, HTTPException

from config import settings
from deps.auth import bind_user_context
from models.schemas import (
    CandidateProfile, JobFeedResponse, JobListing, JobPreferences,
    LiveJobsResponse, UserPublic, now_iso,
)

from services.guardrails import filter_job_sources, sanitize_search_query
from services.guardrails.constants import ALLOWED_JOB_SOURCES
from services.guardrails.ids import sanitize_job_id
from services.job_sanitize import sanitize_job_listing
from services.location_filter import job_matches_location
from services import storage_service as store
from services.job_feed_service import SOURCES, fetch_job_feed
from services.location_registry import match_location_profile
from services.job_recency import filter_jobs_by_recency, sort_jobs_for_display
from services.job_match_scorer import score_job_for_profile

router = APIRouter(prefix="/api/jobs", tags=["jobs"], dependencies=[Depends(bind_user_context)])


def _derive_search_query(profile: CandidateProfile | None, prefs: JobPreferences) -> str:
    if prefs.search_query.strip():
        return prefs.search_query.strip()
    if profile and profile.experience:
        return profile.experience[0].role
    if profile and profile.skills:
        return profile.skills[0].name
    return "software engineer"


async def _build_live_feed(force_refresh: bool = False) -> LiveJobsResponse:
    data = await store.load_data()
    prefs = data.job_preferences
    profile = data.current_profile_state

    if (
        not force_refresh
        and data.cached_live_jobs
        and data.live_jobs_fetched_at
    ):
        jobs = [JobListing(**j) if isinstance(j, dict) else j for j in data.cached_live_jobs]
        jobs = [sanitize_job_listing(j) for j in jobs]
        loc = prefs.location or settings.linkedin_default_location
        jobs = [j for j in jobs if job_matches_location(j, loc)]
        if remote_only := prefs.remote_only:
            jobs = [j for j in jobs if j.remote]
        jobs = filter_jobs_by_recency(jobs, prefs.posted_within)
        scored = [score_job_for_profile(j, profile) for j in jobs]
        scored = sort_jobs_for_display(scored, profile=profile)
        return LiveJobsResponse(
            total=len(scored),
            sources=prefs.preferred_sources,
            jobs=scored,
            fetched_at=data.live_jobs_fetched_at or now_iso(),
            from_cache=True,
            preferences=prefs,
        )

    search = _derive_search_query(profile, prefs)
    jobs, used_sources = await fetch_job_feed(
        search=search,
        sources=prefs.preferred_sources or list(SOURCES),
        limit_per_source=18,
        remote_only=prefs.remote_only,
        location=prefs.location or settings.linkedin_default_location,
        posted_within=prefs.posted_within,
    )

    scored: list[JobListing] = []
    for job in jobs:
        scored.append(score_job_for_profile(job, profile))
    scored = filter_jobs_by_recency(scored, prefs.posted_within)
    scored = sort_jobs_for_display(scored, profile=profile)

    fetched_at = now_iso()
    await store.cache_live_jobs([j.model_dump() for j in scored], fetched_at)

    return LiveJobsResponse(
        total=len(scored),
        sources=used_sources,
        jobs=scored,
        fetched_at=fetched_at,
        from_cache=False,
        preferences=prefs,
    )


@router.get("/live", response_model=LiveJobsResponse)
async def get_live_jobs(
    refresh: bool = Query(False, description="Force fresh fetch from LinkedIn, Greenhouse, Hiring Cafe"),
):
    """Authenticated live job feed — personalized from profile + preferences."""
    return await _build_live_feed(force_refresh=refresh)


@router.get("", response_model=JobFeedResponse)
async def get_job_feed(
    search: str = Query(""),
    sources: str = Query(""),
    limit: int = Query(20, ge=1, le=60),
    remote_only: bool = Query(False),
    location: str = Query(""),
    match: bool = Query(True),
    user: UserPublic = Depends(bind_user_context),
):
    source_list = [s.strip() for s in sources.split(",") if s.strip()] if sources else None
    if source_list:
        source_list = filter_job_sources(source_list)
    data = await store.load_data()
    loc = sanitize_search_query(location) or data.job_preferences.location or settings.linkedin_default_location
    q = sanitize_search_query(search) or _derive_search_query(data.current_profile_state, data.job_preferences)
    posted_within = data.job_preferences.posted_within

    jobs, used_sources = await fetch_job_feed(
        search=q,
        sources=source_list,
        limit_per_source=limit,
        remote_only=remote_only,
        location=loc,
        posted_within=posted_within,
    )

    profile = data.current_profile_state if match else None
    scored = [score_job_for_profile(j, profile) for j in jobs]
    scored = filter_jobs_by_recency(scored, posted_within)
    scored = sort_jobs_for_display(scored, profile=profile)

    return JobFeedResponse(total=len(scored), sources=used_sources, jobs=scored)


@router.get("/sources")
async def list_job_sources(location: str = Query("", description="Resolve regional platforms for a location")):
    profile = match_location_profile(location)
    return {
        "sources": list(SOURCES),
        "regional_sources": list(profile.fetch_sources),
        "researched_platforms": list(profile.researched_platforms),
        "descriptions": {
            "linkedin": "Live LinkedIn job postings",
            "greenhouse": "Real Greenhouse career page listings",
            "hiringcafe": "Hiring Cafe multi-board aggregator",
            "shine": "Shine.com — India job board (live API)",
            "naukri": "Naukri.com — India's largest job portal",
            "indeed_india": "Indeed India — multi-board aggregator",
        },
        "greenhouse_boards": settings.greenhouse_boards,
    }


@router.get("/platforms")
async def resolve_platforms(location: str = Query(..., min_length=1)):
    """Return top platforms for a location (registry + guardrailed agent metadata)."""
    from agents.location_platform_agent import resolve_platforms_for_location

    sources, rationale, researched = await resolve_platforms_for_location(location, use_ai=False)
    return {
        "location": location,
        "fetch_sources": sources,
        "researched_platforms": list(researched),
        "rationale": rationale,
    }


@router.get("/{job_id:path}", response_model=JobListing)
async def get_job(
    job_id: str,
    match: bool = Query(True),
    user: UserPublic = Depends(bind_user_context),
):
    try:
        safe_job_id = sanitize_job_id(job_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    source = safe_job_id.split(":", 1)[0] if ":" in safe_job_id else ""
    if source not in ALLOWED_JOB_SOURCES:
        raise HTTPException(404, "Unknown job source")

    jobs, _ = await fetch_job_feed(sources=[source], limit_per_source=50)
    found = next((j for j in jobs if j.id == safe_job_id), None)
    if not found:
        raise HTTPException(404, "Job not found")

    if match:
        data = await store.load_data()
        found = score_job_for_profile(found, data.current_profile_state)
    return found
