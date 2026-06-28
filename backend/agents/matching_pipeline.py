"""Step-by-step job matching pipeline — profile vs job description.

Pipeline (3 LLM steps):
  1. Extract structured requirements from the JD
  2. Map candidate experience/projects/skills to those requirements
  3. Score fit dimensions and produce final match analysis
"""
from models.schemas import CandidateProfile, MatchResponse, MatchStep
from agents.shared.profile_context import build_profile_context
from services.guardrails import (
    clamp_percentage,
    sanitize_ai_string_list,
    sanitize_ai_text,
    sanitize_company_role,
    wrap_untrusted_content,
)
from services.openai_service import chat_json

_STEP1_SYSTEM = """You are an expert job description analyst.
STEP 1 — Extract structured requirements from the job description ONLY.
Do not evaluate the candidate yet.

Return ONLY valid JSON:
{
  "company": "hiring company or empty string",
  "role": "job title or empty string",
  "seniority": "e.g. junior, mid, senior, staff, lead",
  "must_have_skills": ["required technical skills"],
  "nice_to_have_skills": ["preferred but optional skills"],
  "key_responsibilities": ["3-6 core responsibilities from the JD"],
  "domain_keywords": ["industry/domain terms e.g. fintech, healthcare"]
}
Focus on what the employer explicitly requires — not generic filler."""

_STEP2_SYSTEM = """You are an expert career matcher.
STEP 2 — Map the candidate's REAL experience to the extracted job requirements.
Use ONLY evidence from the candidate profile. Do not invent employers, projects, or skills.

Return ONLY valid JSON:
{
  "experience_matches": [
    {"requirement": "from JD", "evidence": "specific role/project bullet", "strength": "strong|moderate|weak"}
  ],
  "project_matches": [
    {"project": "name", "relevant_to": "which JD requirement it supports"}
  ],
  "skill_evidence": [
    {"skill": "skill name", "source": "experience|project|listed", "note": "brief evidence"}
  ],
  "gaps": ["requirements with weak or no evidence"]
}"""

_STEP3_SYSTEM = """You are an expert ATS and hiring analyst.
STEP 3 — Synthesize a final match score using the JD requirements and evidence mapping.
Weight: skills 35%, experience alignment 35%, projects 15%, domain fit 15%.

Return ONLY valid JSON:
{
  "match_percentage": 72.5,
  "score_breakdown": {"skills": 80, "experience": 70, "projects": 65, "domain": 75},
  "job_required_skills": ["all key skills the JD asks for"],
  "matched_skills": ["skills the candidate clearly has for this role"],
  "missing_skills": ["important gaps to address"],
  "experience_highlights": ["2-4 strongest evidence bullets tied to this JD"],
  "matching_steps": [
    {"step": 1, "title": "Extract JD requirements", "summary": "1 sentence on what the role needs"},
    {"step": 2, "title": "Map experience evidence", "summary": "1 sentence on strongest alignment"},
    {"step": 3, "title": "Calculate fit score", "summary": "1 sentence explaining the overall score"}
  ],
  "recommendation": "2 sentences: strengths for this application + how to close gaps"
}
match_percentage must reflect semantic fit, not keyword stuffing alone."""


def _parse_steps(raw: object) -> list[MatchStep]:
    if not isinstance(raw, list):
        return []
    steps: list[MatchStep] = []
    for item in raw[:5]:
        if not isinstance(item, dict):
            continue
        steps.append(
            MatchStep(
                step=int(item.get("step", len(steps) + 1)),
                title=sanitize_ai_text(item.get("title", ""), max_len=80),
                summary=sanitize_ai_text(item.get("summary", ""), max_len=300),
            )
        )
    return steps


def _parse_score_breakdown(raw: object) -> dict[str, float]:
    if not isinstance(raw, dict):
        return {}
    keys = ("skills", "experience", "projects", "domain")
    return {k: clamp_percentage(raw.get(k, 0)) for k in keys if k in raw}


async def run_matching_pipeline(
    profile: CandidateProfile,
    job_description: str,
    company_hint: str = "",
    role_hint: str = "",
) -> MatchResponse:
    profile_ctx = build_profile_context(profile, include_confidence=True)
    jd_block = wrap_untrusted_content("job_description", job_description)

    hints = ""
    if company_hint:
        hints += f"\nUser-provided company (authoritative): {sanitize_company_role(company_hint)}"
    if role_hint:
        hints += f"\nUser-provided role (authoritative): {sanitize_company_role(role_hint)}"

    # ── Step 1: Extract JD requirements ─────────────────────────────────────
    step1 = await chat_json(
        _STEP1_SYSTEM,
        f"{hints}\n\n{jd_block}",
        temperature=0.2,
        agent="match_step1_jd_extract",
    )

    # ── Step 2: Map candidate evidence ──────────────────────────────────────
    step2_payload = (
        f"JOB REQUIREMENTS (from Step 1):\n{step1}\n\n"
        f"CANDIDATE PROFILE:\n{profile_ctx}"
    )
    step2 = await chat_json(
        _STEP2_SYSTEM,
        step2_payload,
        temperature=0.25,
        agent="match_step2_evidence",
    )

    # ── Step 3: Final score & recommendations ───────────────────────────────
    step3_payload = (
        f"JOB REQUIREMENTS:\n{step1}\n\n"
        f"EVIDENCE MAPPING:\n{step2}\n\n"
        f"CANDIDATE PROFILE:\n{profile_ctx}"
    )
    step3 = await chat_json(
        _STEP3_SYSTEM,
        step3_payload,
        temperature=0.3,
        agent="match_step3_score",
    )

    company = sanitize_company_role(company_hint) or sanitize_company_role(
        str(step1.get("company") or step3.get("company", ""))
    )
    role = sanitize_company_role(role_hint) or sanitize_company_role(
        str(step1.get("role") or step3.get("role", ""))
    )

    steps = _parse_steps(step3.get("matching_steps"))
    if not steps:
        steps = [
            MatchStep(step=1, title="Extract JD requirements", summary=sanitize_ai_text(step1.get("seniority", "Requirements parsed"), 200)),
            MatchStep(step=2, title="Map experience evidence", summary=f"{len(step2.get('experience_matches', []))} experience alignments found"),
            MatchStep(step=3, title="Calculate fit score", summary=sanitize_ai_text(step3.get("recommendation", ""), 200)),
        ]

    return MatchResponse(
        match_percentage=clamp_percentage(step3.get("match_percentage", 0)),
        matched_skills=sanitize_ai_string_list(step3.get("matched_skills")),
        missing_skills=sanitize_ai_string_list(step3.get("missing_skills")),
        job_required_skills=sanitize_ai_string_list(
            step3.get("job_required_skills") or step1.get("must_have_skills")
        ),
        recommendation=sanitize_ai_text(step3.get("recommendation", ""), max_len=600),
        company=company,
        role=role,
        matching_steps=steps,
        experience_highlights=sanitize_ai_string_list(step3.get("experience_highlights"), max_items=6),
        score_breakdown=_parse_score_breakdown(step3.get("score_breakdown")),
    )
