"""Agent 2 – Job Matching Agent
Analyzes a JD against the current profile → match %, required/matched/missing skills,
and auto-extracts the company name and role from the JD when possible.
"""
from models.schemas import CandidateProfile, MatchResponse
from services.openai_service import chat_json


_SYSTEM = """You are an expert ATS and job-matching analyst.
Given a candidate profile (skills with confidence scores) and a job description,
analyze the semantic fit. Also extract the hiring company name and job role/title
directly from the job description text when they are present.

Return ONLY valid JSON:
{
  "company": "extracted company name or empty string",
  "role": "extracted job title or empty string",
  "match_percentage": 72.5,
  "job_required_skills": ["Python", "Docker", "SQL"],
  "matched_skills": ["Python", "SQL"],
  "missing_skills": ["Docker", "Kubernetes"],
  "recommendation": "Short 1-2 sentence advice on how to strengthen this application."
}
match_percentage (0-100) is a semantic fit score considering skill overlap, project
relevance, experience alignment, and context similarity — not just keyword overlap.
"""


async def match_job(
    profile: CandidateProfile,
    job_description: str,
    company_hint: str = "",
    role_hint: str = "",
) -> MatchResponse:
    skill_list = [f"{s.name} ({s.confidence:.0f}% confidence)" for s in profile.skills]
    candidate_ctx = (
        f"Candidate: {profile.name}\n"
        f"Experience level: {len(profile.experience)} role(s)\n"
        f"Domains: {', '.join(profile.domains)}\n"
        f"Skills: {', '.join(skill_list)}\n"
        f"Projects: {', '.join(p.name for p in profile.projects)}\n"
        f"Experience: {', '.join(f'{e.role} at {e.company}' for e in profile.experience)}"
    )

    hints = ""
    if company_hint:
        hints += f"\nUser-provided company (authoritative): {company_hint}"
    if role_hint:
        hints += f"\nUser-provided role (authoritative): {role_hint}"

    payload = f"{candidate_ctx}{hints}\n\n---\nJob Description:\n{job_description[:4000]}"
    data = await chat_json(_SYSTEM, payload)

    # Prefer user-provided values; fall back to AI-extracted.
    company = company_hint.strip() or str(data.get("company", "")).strip()
    role = role_hint.strip() or str(data.get("role", "")).strip()

    return MatchResponse(
        match_percentage=float(data.get("match_percentage", 0)),
        matched_skills=data.get("matched_skills", []),
        missing_skills=data.get("missing_skills", []),
        job_required_skills=data.get("job_required_skills", []),
        recommendation=data.get("recommendation", ""),
        company=company,
        role=role,
    )
