"""Agent 3 – Resume Generation Agent
Produces a tailored summary and reordered skills list, then generates PDF via ReportLab.
"""
from models.schemas import CandidateProfile
from services.openai_service import chat_json
from services.pdf_service import generate_resume_pdf


_SYSTEM = """You are a professional resume writer.
Given a candidate profile and a job description, produce a tailored resume package.
Return ONLY valid JSON:
{
  "tailored_summary": "2-3 sentence professional summary optimized for this role.",
  "ordered_skills": ["most relevant skill", "second most relevant", ...],
  "highlighted_projects": ["Project A", "Project B"],
  "key_achievements": ["Achievement 1", "Achievement 2"]
}
ordered_skills: list ALL candidate skills reordered with most JD-relevant first.
"""


async def generate_tailored_resume(
    profile: CandidateProfile,
    job_description: str,
) -> bytes:
    skill_names = [s.name for s in profile.skills]
    candidate_ctx = (
        f"Name: {profile.name}\n"
        f"Skills: {', '.join(skill_names)}\n"
        f"Summary: {profile.summary}\n"
        f"Projects: {', '.join(p.name for p in profile.projects)}\n"
        f"Experience: {', '.join(f'{e.role} at {e.company}' for e in profile.experience)}"
    )

    payload = f"{candidate_ctx}\n\n---\nJob Description:\n{job_description[:4000]}"
    data = await chat_json(_SYSTEM, payload, temperature=0.4)

    tailored_summary = data.get("tailored_summary", profile.summary)
    ordered_skills = data.get("ordered_skills", skill_names)

    # Merge: ensure all profile skills are included
    profile_skill_names = {s.name.lower() for s in profile.skills}
    extra = [s for s in ordered_skills if s.lower() not in profile_skill_names]
    final_skills = ordered_skills + extra

    return generate_resume_pdf(profile, tailored_summary, final_skills)
