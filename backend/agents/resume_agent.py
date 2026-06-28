"""Agent 3 – Resume Generation Agent
Multi-agent pipeline → LaTeX source → PDF via PyLaTeX.
"""
from typing import Optional

from models.schemas import (
    CandidateProfile,
    MatchContextInput,
    ResumePreviewResponse,
    ResumeSnapshot,
    ResumeStyle,
)
from agents.resume_pipeline import run_resume_pipeline
from services.latex_service import generate_resume_pdf_from_package


async def build_resume_package(
    profile: CandidateProfile,
    job_description: str,
    style: Optional[ResumeStyle] = None,
    match: Optional[MatchContextInput] = None,
    original: Optional[ResumeSnapshot] = None,
) -> ResumePreviewResponse:
    return await run_resume_pipeline(profile, job_description, style, match, original)


async def generate_tailored_resume(
    profile: CandidateProfile,
    job_description: str,
    style: Optional[ResumeStyle] = None,
    match: Optional[MatchContextInput] = None,
    original: Optional[ResumeSnapshot] = None,
) -> tuple[bytes, str]:
    """Return (pdf_bytes, latex_source)."""
    package = await build_resume_package(
        profile, job_description, style, match, original,
    )
    accent = style.accent_hex if style else "#10b981"
    pdf_bytes, latex_source = generate_resume_pdf_from_package(
        profile, package, accent_hex=accent, latex_source=package.latex_source,
    )
    return pdf_bytes, latex_source
