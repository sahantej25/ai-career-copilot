"""Step-by-step resume tailoring pipeline — professional JD-aligned resume package.

Pipeline (2 LLM steps):
  1. Plan tailoring — which experience/projects to emphasize for this JD
  2. Produce final package — rewritten summary, bullets, skills order, achievements
"""
from typing import Optional

from models.schemas import (
    CandidateProfile,
    MatchContextInput,
    MatchStep,
    ResumePreviewResponse,
    ResumeStyle,
    TailoredExperienceEntry,
)
from agents.shared.profile_context import build_profile_context
from services.guardrails import (
    sanitize_ai_string_list,
    sanitize_ai_text,
    scrub_forbidden_phrases,
    wrap_untrusted_content,
)
from services.openai_service import chat_json

_STEP1_SYSTEM = """You are a senior resume strategist.
STEP 1 — Plan how to tailor this candidate's resume for the target job.
Use the match analysis and job description. Only use REAL candidate data.

Return ONLY valid JSON:
{
  "target_titles": ["how to position the candidate e.g. Senior Frontend Engineer"],
  "priority_experience": [
    {"company": "...", "role": "...", "why_relevant": "1 sentence tied to JD"}
  ],
  "priority_projects": ["project names most relevant to JD"],
  "keywords_to_weave": ["6-10 JD keywords to naturally include"],
  "tailoring_steps": [
    {"step": 1, "title": "Analyze role fit", "summary": "1 sentence"},
    {"step": 2, "title": "Plan experience emphasis", "summary": "1 sentence"}
  ]
}"""

_STEP2_SYSTEM = """You are a professional resume writer specializing in ATS-optimized, role-specific resumes.
STEP 2 — Write the tailored resume package for this exact job.

Rules:
- Rewrite experience bullets to highlight JD-relevant impact (metrics, action verbs, keywords).
- Do NOT invent employers, degrees, tools, or achievements not supported by the candidate profile.
- Never mention confidence scores, system notes, or internal metadata.
- Summary must sound natural and senior — not keyword-stuffed.
- ordered_skills: ALL candidate skills, most JD-relevant first.

Return ONLY valid JSON:
{
  "tailored_summary": "2-3 sentence professional summary for THIS role",
  "ordered_skills": ["skill1", "skill2"],
  "highlighted_projects": ["Project A"],
  "key_achievements": ["2-4 impact bullets for summary or experience"],
  "tailored_experience": [
    {
      "company": "exact company from profile",
      "role": "exact or slightly refined role title",
      "duration": "from profile",
      "bullets": ["rewritten bullet 1", "rewritten bullet 2"]
    }
  ],
  "emphasis": "1 sentence on what this resume emphasizes",
  "tailoring_steps": [
    {"step": 3, "title": "Rewrite experience bullets", "summary": "1 sentence"},
    {"step": 4, "title": "Finalize tailored package", "summary": "1 sentence"}
  ]
}
Include ALL profile experience entries in tailored_experience, reordered with most relevant first.
Each entry should have 2-4 rewritten bullets when original bullets exist."""


def _parse_steps(raw: object) -> list[MatchStep]:
    if not isinstance(raw, list):
        return []
    out: list[MatchStep] = []
    for item in raw[:6]:
        if not isinstance(item, dict):
            continue
        out.append(
            MatchStep(
                step=int(item.get("step", len(out) + 1)),
                title=sanitize_ai_text(item.get("title", ""), max_len=80),
                summary=sanitize_ai_text(item.get("summary", ""), max_len=300),
            )
        )
    return out


def _parse_tailored_experience(raw: object, profile: CandidateProfile) -> list[TailoredExperienceEntry]:
    if not isinstance(raw, list):
        return _fallback_experience(profile)
    entries: list[TailoredExperienceEntry] = []
    for item in raw[:8]:
        if not isinstance(item, dict):
            continue
        bullets = sanitize_ai_string_list(item.get("bullets"), max_items=6)
        if not bullets:
            continue
        entries.append(
            TailoredExperienceEntry(
                company=sanitize_ai_text(item.get("company", ""), max_len=120),
                role=sanitize_ai_text(item.get("role", ""), max_len=120),
                duration=sanitize_ai_text(item.get("duration", ""), max_len=80),
                bullets=bullets,
            )
        )
    return entries or _fallback_experience(profile)


def _fallback_experience(profile: CandidateProfile) -> list[TailoredExperienceEntry]:
    return [
        TailoredExperienceEntry(
            company=exp.company,
            role=exp.role,
            duration=exp.duration,
            bullets=[sanitize_ai_text(b, max_len=400) for b in exp.description[:4] if b],
        )
        for exp in profile.experience[:6]
        if exp.description
    ]


def _match_context_block(match: Optional[MatchContextInput]) -> str:
    if not match:
        return "No prior match analysis — infer alignment from JD and profile."
    lines = [
        f"Match score: {match.match_percentage:.0f}%",
        f"Matched skills: {', '.join(match.matched_skills)}",
        f"Missing skills: {', '.join(match.missing_skills)}",
        f"JD required skills: {', '.join(match.job_required_skills)}",
    ]
    if match.experience_highlights:
        lines.append("Strongest evidence: " + "; ".join(match.experience_highlights[:4]))
    if match.score_breakdown:
        breakdown = ", ".join(f"{k}={v:.0f}" for k, v in match.score_breakdown.items())
        lines.append(f"Score breakdown: {breakdown}")
    return "\n".join(lines)


async def run_resume_pipeline(
    profile: CandidateProfile,
    job_description: str,
    style: Optional[ResumeStyle] = None,
    match: Optional[MatchContextInput] = None,
) -> ResumePreviewResponse:
    sorted_skills = sorted(profile.skills, key=lambda s: s.confidence, reverse=True)
    skill_names = [s.name for s in sorted_skills]
    profile_ctx = build_profile_context(profile, include_confidence=False)
    jd_block = wrap_untrusted_content("job_description", job_description)
    match_block = _match_context_block(match)

    style_ctx = ""
    if style:
        style_ctx = (
            f"\nReference style — tone: {sanitize_ai_text(style.tone, 120)}; "
            f"section order: {', '.join(style.section_order)}; "
            f"notes: {sanitize_ai_text(style.notes, 300)}"
        )

    # ── Step 1: Tailoring plan ──────────────────────────────────────────────
    plan = await chat_json(
        _STEP1_SYSTEM,
        f"MATCH ANALYSIS:\n{match_block}\n\n{jd_block}\n\nCANDIDATE:\n{profile_ctx}{style_ctx}",
        temperature=0.3,
        agent="resume_step1_plan",
    )

    # ── Step 2: Final tailored package ──────────────────────────────────────
    package = await chat_json(
        _STEP2_SYSTEM,
        (
            f"TAILORING PLAN:\n{plan}\n\n"
            f"MATCH ANALYSIS:\n{match_block}\n\n"
            f"{jd_block}\n\n"
            f"CANDIDATE PROFILE:\n{profile_ctx}{style_ctx}"
        ),
        temperature=0.4,
        agent="resume_step2_package",
    )

    ordered = sanitize_ai_string_list(package.get("ordered_skills")) or skill_names
    seen = {s.lower() for s in ordered}
    ordered += [s for s in skill_names if s.lower() not in seen]

    summary = scrub_forbidden_phrases(
        sanitize_ai_text(package.get("tailored_summary", profile.summary), max_len=800)
    )

    steps = _parse_steps(plan.get("tailoring_steps")) + _parse_steps(package.get("tailoring_steps"))

    return ResumePreviewResponse(
        tailored_summary=summary or profile.summary,
        ordered_skills=ordered,
        highlighted_projects=sanitize_ai_string_list(
            package.get("highlighted_projects") or plan.get("priority_projects")
        ),
        key_achievements=sanitize_ai_string_list(package.get("key_achievements")),
        emphasis=scrub_forbidden_phrases(sanitize_ai_text(package.get("emphasis", ""), max_len=300)),
        tailored_experience=_parse_tailored_experience(package.get("tailored_experience"), profile),
        tailoring_steps=steps,
    )
