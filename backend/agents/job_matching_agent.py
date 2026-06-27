"""Agent 2 – Job Matching Agent
Analyzes a JD against the current profile → match %, missing skills, recommendations.
"""
from models.schemas import CandidateProfile, MatchResponse
from services.openai_service import chat_json


_SYSTEM = """You are an expert ATS and job-matching analyst.
Given a candidate profile (skills with confidence scores) and a job description,
return ONLY valid JSON:
{
  "match_percentage": 72.5,
  "job_required_skills": ["Python", "Docker", "SQL"],
  "matched_skills": ["Python", "SQL"],
  "missing_skills": ["Docker", "Kubernetes"],
  "recommendation": "Short 1-2 sentence advice on how to strengthen this application."
}
match_percentage (0-100) is a semantic fit score — not just keyword overlap.
Consider experience level, domain alignment, and transferable skills.
"""


async def match_job(profile: CandidateProfile, job_description: str) -> MatchResponse:
    skill_list = [
        f"{s.name} ({s.confidence:.0f}% confidence)"
        for s in profile.skills
    ]
    candidate_ctx = (
        f"Candidate: {profile.name}\n"
        f"Domains: {', '.join(profile.domains)}\n"
        f"Skills: {', '.join(skill_list)}\n"
        f"Projects: {', '.join(p.name for p in profile.projects)}\n"
        f"Experience: {', '.join(f'{e.role} at {e.company}' for e in profile.experience)}"
    )

    payload = f"{candidate_ctx}\n\n---\nJob Description:\n{job_description[:4000]}"
    data = await chat_json(_SYSTEM, payload)

    return MatchResponse(
        match_percentage=float(data.get("match_percentage", 0)),
        matched_skills=data.get("matched_skills", []),
        missing_skills=data.get("missing_skills", []),
        job_required_skills=data.get("job_required_skills", []),
        recommendation=data.get("recommendation", ""),
    )
