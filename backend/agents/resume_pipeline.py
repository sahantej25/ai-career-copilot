"""Step-by-step resume tailoring pipeline — professional JD-aligned resume package.

Pipeline (2 LLM steps):
  1. Plan tailoring — which experience/projects to emphasize for this JD
  2. Produce final package — rewritten summary, bullets, skills order, achievements
"""
from typing import Optional

from models.schemas import (
    CandidateProfile,
    Experience,
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
STEP 2 — Tailor the candidate's EXISTING resume for this exact job while preserving its structure.

CRITICAL STRUCTURE RULES:
- Keep the SAME employers, roles, durations, projects, and education as the original profile.
- Do NOT remove roles or collapse sections into a shorter generic version.
- For each experience entry, output ONE rewritten bullet for EVERY original bullet (same count).
  If the original role has 6 bullets, you MUST return 6 tailored bullets — never fewer.
- Reorder experience entries so the most JD-relevant roles appear first, but include ALL roles.
- Rewrite bullets in place: keep concrete facts, tools, systems, scope, and metrics from the source.
  Refine wording for impact and weave JD keywords naturally — do NOT replace specifics with generic filler.
- Avoid vague phrases like "worked on various tasks", "helped the team", or "responsible for" unless the source used them.

Content rules:
- Do NOT invent employers, degrees, tools, or achievements not supported by the candidate profile.
- Never mention confidence scores, system notes, or internal metadata.
- Summary: 3-4 sentences, senior and specific to THIS role — not keyword-stuffed.
- ordered_skills: ALL candidate skills, most JD-relevant first.

Return ONLY valid JSON:
{
  "tailored_summary": "3-4 sentence professional summary for THIS role",
  "ordered_skills": ["skill1", "skill2"],
  "highlighted_projects": ["Project A"],
  "key_achievements": ["3-5 high-impact bullets drawn from rewritten experience"],
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
}"""


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


def _experience_key(company: str, role: str) -> tuple[str, str]:
    return company.strip().lower(), role.strip().lower()


def _find_profile_experience(profile: CandidateProfile, company: str, role: str) -> Experience | None:
    key = _experience_key(company, role)
    for exp in profile.experience:
        if _experience_key(exp.company, exp.role) == key:
            return exp
    return None


def _ensure_bullet_count(
    tailored: list[str],
    original: list[str],
    *,
    max_bullets: int = 10,
) -> list[str]:
    """Keep AI rewrites first; pad with originals if the model dropped bullets."""
    cleaned = [sanitize_ai_text(b, max_len=400) for b in tailored if b and str(b).strip()]
    if not original:
        return cleaned[:max_bullets]
    target = min(len(original), max_bullets)
    if len(cleaned) >= target:
        return cleaned[:max_bullets]
    seen = {b.lower() for b in cleaned}
    for bullet in original:
        if len(cleaned) >= target:
            break
        text = sanitize_ai_text(bullet, max_len=400)
        if text and text.lower() not in seen:
            cleaned.append(text)
            seen.add(text.lower())
    return cleaned[:max_bullets]


def _merge_tailored_with_profile(
    tailored: list[TailoredExperienceEntry],
    profile: CandidateProfile,
) -> list[TailoredExperienceEntry]:
    """Ensure every original role appears with full bullet depth."""
    merged: list[TailoredExperienceEntry] = []
    seen: set[tuple[str, str]] = set()

    for entry in tailored:
        key = _experience_key(entry.company, entry.role)
        seen.add(key)
        original = _find_profile_experience(profile, entry.company, entry.role)
        bullets = _ensure_bullet_count(
            entry.bullets,
            original.description if original else [],
        )
        merged.append(
            TailoredExperienceEntry(
                company=entry.company or (original.company if original else ""),
                role=entry.role or (original.role if original else ""),
                duration=entry.duration or (original.duration if original else ""),
                bullets=bullets,
            )
        )

    for exp in profile.experience:
        key = _experience_key(exp.company, exp.role)
        if key in seen:
            continue
        merged.append(
            TailoredExperienceEntry(
                company=exp.company,
                role=exp.role,
                duration=exp.duration,
                bullets=_ensure_bullet_count(exp.description, exp.description),
            )
        )

    return merged


def _parse_tailored_experience(raw: object, profile: CandidateProfile) -> list[TailoredExperienceEntry]:
    if not isinstance(raw, list):
        return _fallback_experience(profile)
    entries: list[TailoredExperienceEntry] = []
    for item in raw[:12]:
        if not isinstance(item, dict):
            continue
        bullets = sanitize_ai_string_list(item.get("bullets"), max_items=10)
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
    if not entries:
        return _fallback_experience(profile)
    return _merge_tailored_with_profile(entries, profile)


def _fallback_experience(profile: CandidateProfile) -> list[TailoredExperienceEntry]:
    return [
        TailoredExperienceEntry(
            company=exp.company,
            role=exp.role,
            duration=exp.duration,
            bullets=_ensure_bullet_count(exp.description, exp.description),
        )
        for exp in profile.experience[:12]
        if exp.description
    ]


def _build_original_experience_block(profile: CandidateProfile) -> str:
    if not profile.experience:
        return "No experience entries."
    lines = ["ORIGINAL EXPERIENCE (preserve structure and bullet count):"]
    for exp in profile.experience:
        lines.append(f"  • {exp.role} at {exp.company} ({exp.duration}) — {len(exp.description)} bullets")
        for i, bullet in enumerate(exp.description[:10], 1):
            if bullet.strip():
                lines.append(f"      {i}. {bullet.strip()}")
    return "\n".join(lines)


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
    original_exp_block = _build_original_experience_block(profile)
    package = await chat_json(
        _STEP2_SYSTEM,
        (
            f"TAILORING PLAN:\n{plan}\n\n"
            f"MATCH ANALYSIS:\n{match_block}\n\n"
            f"{original_exp_block}\n\n"
            f"{jd_block}\n\n"
            f"CANDIDATE PROFILE:\n{profile_ctx}{style_ctx}"
        ),
        temperature=0.35,
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
