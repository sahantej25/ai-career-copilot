"""Agent 3 – Resume Generation Agent
Builds a tailored resume package (summary + reordered skills + highlighted projects)
and renders a clean PDF via ReportLab. Honors an optional reference-resume style.

The generated resume NEVER exposes internal system data (confidence scores, flags,
rejection annotations). Skills weakened by rejection analysis simply sink in priority.
"""
from typing import Optional

from models.schemas import CandidateProfile, ResumeStyle, ResumePreviewResponse
from services.guardrails import (
    sanitize_ai_string_list,
    sanitize_ai_text,
    scrub_forbidden_phrases,
    wrap_untrusted_content,
)
from services.openai_service import chat_json
from services.pdf_service import generate_resume_pdf


_SYSTEM = """You are a professional resume writer.
Given a candidate profile and a job description, produce a tailored resume package.
Return ONLY valid JSON:
{
  "tailored_summary": "2-3 sentence professional summary optimized for this role.",
  "ordered_skills": ["most relevant skill", "second most relevant", ...],
  "highlighted_projects": ["Project A", "Project B"],
  "key_achievements": ["Achievement 1", "Achievement 2"],
  "emphasis": "1 sentence describing what this resume emphasizes for this role."
}
ordered_skills: list ALL candidate skills reordered with the most JD-relevant first.
Present the candidate at their strongest. Never mention scores, weaknesses, or system notes.
If a reference style/tone is provided, match that tone.
"""


async def build_resume_package(
    profile: CandidateProfile,
    job_description: str,
    style: Optional[ResumeStyle] = None,
) -> ResumePreviewResponse:
    sorted_skills = sorted(profile.skills, key=lambda s: s.confidence, reverse=True)
    skill_names = [s.name for s in sorted_skills]

    style_ctx = ""
    if style:
        style_ctx = (
            f"\nReference style to emulate — tone: {sanitize_ai_text(style.tone, 120)}; "
            f"section order: {', '.join(style.section_order)}; "
            f"notes: {sanitize_ai_text(style.notes, 300)}"
        )

    candidate_ctx = (
        f"Name: {profile.name}\n"
        f"Summary: {profile.summary}\n"
        f"Skills (strongest first): {', '.join(skill_names)}\n"
        f"Projects: {', '.join(p.name for p in profile.projects)}\n"
        f"Experience: {', '.join(f'{e.role} at {e.company}' for e in profile.experience)}"
        f"{style_ctx}"
    )

    jd_block = wrap_untrusted_content("job_description", job_description)
    payload = f"{candidate_ctx}\n\n---\n{jd_block}"
    data = await chat_json(_SYSTEM, payload, temperature=0.4, agent="resume_generation")

    ordered = sanitize_ai_string_list(data.get("ordered_skills")) or skill_names
    seen = {s.lower() for s in ordered}
    ordered += [s for s in skill_names if s.lower() not in seen]

    summary = scrub_forbidden_phrases(
        sanitize_ai_text(data.get("tailored_summary", profile.summary), max_len=800)
    )

    return ResumePreviewResponse(
        tailored_summary=summary or profile.summary,
        ordered_skills=ordered,
        highlighted_projects=sanitize_ai_string_list(data.get("highlighted_projects")),
        key_achievements=sanitize_ai_string_list(data.get("key_achievements")),
        emphasis=scrub_forbidden_phrases(sanitize_ai_text(data.get("emphasis", ""), max_len=300)),
    )


async def generate_tailored_resume(
    profile: CandidateProfile,
    job_description: str,
    style: Optional[ResumeStyle] = None,
) -> bytes:
    package = await build_resume_package(profile, job_description, style)
    return generate_resume_pdf(
        profile,
        package.tailored_summary,
        package.ordered_skills,
        highlighted_projects=package.highlighted_projects,
        section_order=style.section_order if style else None,
        accent_hex=style.accent_hex if style else "#10b981",
    )
