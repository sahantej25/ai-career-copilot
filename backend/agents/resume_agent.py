"""Agent 3 – Resume Generation Agent
Step-by-step pipeline: plan tailoring → rewrite experience → produce PDF package.
"""
from typing import Optional

from models.schemas import (
    CandidateProfile,
    MatchContextInput,
    ResumePreviewResponse,
    ResumeStyle,
)
from agents.resume_pipeline import run_resume_pipeline
from services.pdf_service import generate_resume_pdf


async def build_resume_package(
    profile: CandidateProfile,
    job_description: str,
    style: Optional[ResumeStyle] = None,
    match: Optional[MatchContextInput] = None,
) -> ResumePreviewResponse:
    return await run_resume_pipeline(profile, job_description, style, match)


async def generate_tailored_resume(
    profile: CandidateProfile,
    job_description: str,
    style: Optional[ResumeStyle] = None,
    match: Optional[MatchContextInput] = None,
) -> bytes:
    package = await build_resume_package(profile, job_description, style, match)
    return generate_resume_pdf(
        profile,
        package.tailored_summary,
        package.ordered_skills,
        highlighted_projects=package.highlighted_projects,
        tailored_experience=package.tailored_experience,
        section_order=style.section_order if style else None,
        accent_hex=style.accent_hex if style else "#10b981",
    )
