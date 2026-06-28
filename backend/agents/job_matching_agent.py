"""Agent 2 – Job Matching Agent
Step-by-step pipeline: extract JD → map experience evidence → score fit.
"""
from models.schemas import CandidateProfile, MatchResponse
from agents.matching_pipeline import run_matching_pipeline


async def match_job(
    profile: CandidateProfile,
    job_description: str,
    company_hint: str = "",
    role_hint: str = "",
) -> MatchResponse:
    return await run_matching_pipeline(
        profile, job_description,
        company_hint=company_hint,
        role_hint=role_hint,
    )
