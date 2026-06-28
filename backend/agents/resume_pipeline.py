"""Multi-agent resume tailoring pipeline — preserves original structure & content.

Pipeline (parallel + sequential):
  0. (parallel) Map original resume structure + extract ATS keywords from JD
  1. Plan tailoring emphasis using structure + ATS + match analysis
  2. (parallel) Rewrite summary, reorder skills, tailor each experience role, highlight projects
  3. Merge + validate — every original role/bullet preserved; pad if AI drops content
  4. Build LaTeX source from final package (deterministic, structure-faithful)
"""
import asyncio
from typing import Optional

from models.schemas import (
    CandidateProfile,
    Experience,
    MatchContextInput,
    MatchStep,
    ResumePreviewResponse,
    ResumeSnapshot,
    ResumeStyle,
    TailoredExperienceEntry,
)
from agents.resume_structure_agents import (
    analyze_resume_structure,
    extract_ats_keywords,
    resolve_section_order,
)
from agents.shared.profile_context import build_profile_context
from services.guardrails import (
    sanitize_ai_string_list,
    sanitize_ai_text,
    scrub_forbidden_phrases,
    wrap_untrusted_content,
)
from services.guardrails.constants import MAX_EXPERIENCE_BULLETS
from services.latex_service import build_latex_document
from services.openai_service import chat_json

_STEP1_SYSTEM = """You are a senior resume strategist.
STEP 1 — Plan how to tailor this candidate's resume for the target job.
Use the match analysis, ATS keywords, original structure, and job description.
Only use REAL candidate data — never invent employers, tools, or achievements.

Return ONLY valid JSON:
{
  "target_titles": ["how to position the candidate e.g. Senior Frontend Engineer"],
  "priority_experience": [
    {"company": "...", "role": "...", "why_relevant": "1 sentence tied to JD"}
  ],
  "priority_projects": ["project names most relevant to JD"],
  "keywords_to_weave": ["6-12 ATS keywords to naturally include"],
  "experience_order": [{"company": "...", "role": "..."}],
  "tailoring_steps": [
    {"step": 2, "title": "Analyze role fit", "summary": "1 sentence"},
    {"step": 3, "title": "Plan experience emphasis", "summary": "1 sentence"}
  ]
}"""

_SUMMARY_SYSTEM = """You rewrite ONLY the professional summary for a tailored resume.
Keep 3-4 sentences. Use concrete facts from the candidate profile.
Weave ATS keywords naturally — do NOT keyword-stuff.
Do NOT invent credentials or employers.

Return ONLY valid JSON:
{"tailored_summary": "...", "tailoring_steps": [{"step": 4, "title": "Rewrite summary", "summary": "1 sentence"}]}"""

_SKILLS_SYSTEM = """You reorder the candidate's skill list for ATS alignment with the job.
Include ALL candidate skills — most JD-relevant first. Do NOT drop skills.

Return ONLY valid JSON:
{"ordered_skills": ["skill1", "..."], "tailoring_steps": [{"step": 5, "title": "Reorder skills", "summary": "1 sentence"}]}"""

_ROLE_SYSTEM = """You rewrite experience bullets for ONE role on a tailored resume.
CRITICAL: output EXACTLY the same number of bullets as the original role.
Keep concrete facts, tools, systems, scope, and metrics from the source bullets.
Refine wording for impact and weave JD keywords naturally.
Do NOT replace specifics with generic filler.
Do NOT invent achievements.

Return ONLY valid JSON:
{
  "company": "exact company",
  "role": "exact role",
  "duration": "from profile",
  "bullets": ["rewritten bullet 1", "..."],
  "tailoring_steps": [{"step": 6, "title": "Tailor role bullets", "summary": "1 sentence"}]
}"""

_PROJECTS_SYSTEM = """You select and optionally refine project highlights for this JD.
Include ALL projects from the profile — reorder so JD-relevant projects appear first.
Do NOT invent projects.

Return ONLY valid JSON:
{
  "highlighted_projects": ["project names in priority order"],
  "key_achievements": ["3-5 high-impact bullets drawn from experience/projects"],
  "emphasis": "1 sentence on what this resume emphasizes",
  "tailoring_steps": [{"step": 7, "title": "Highlight projects", "summary": "1 sentence"}]
}"""


def _parse_steps(raw: object) -> list[MatchStep]:
    if not isinstance(raw, list):
        return []
    out: list[MatchStep] = []
    for item in raw[:10]:
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
    max_bullets: int = MAX_EXPERIENCE_BULLETS,
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
    for item in raw[:25]:
        if not isinstance(item, dict):
            continue
        bullets = sanitize_ai_string_list(item.get("bullets"), max_items=MAX_EXPERIENCE_BULLETS)
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
        for exp in profile.experience[:25]
        if exp.description or exp.company
    ]


def _build_original_experience_block(profile: CandidateProfile) -> str:
    if not profile.experience:
        return "No experience entries."
    lines = ["ORIGINAL EXPERIENCE (preserve structure and bullet count):"]
    for exp in profile.experience:
        lines.append(f"  • {exp.role} at {exp.company} ({exp.duration}) — {len(exp.description)} bullets")
        for i, bullet in enumerate(exp.description[:MAX_EXPERIENCE_BULLETS], 1):
            if bullet.strip():
                lines.append(f"      {i}. {bullet.strip()}")
    return "\n".join(lines)


def _build_original_resume_block(snapshot: Optional[ResumeSnapshot]) -> str:
    if not snapshot or not snapshot.raw_text.strip():
        return ""
    return wrap_untrusted_content("original_resume", snapshot.raw_text[:8000])


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


def _order_experience_entries(
    entries: list[TailoredExperienceEntry],
    plan: dict,
    profile: CandidateProfile,
) -> list[TailoredExperienceEntry]:
    """Reorder experience per plan while keeping every role."""
    order_hints = plan.get("experience_order") or plan.get("priority_experience") or []
    priority_keys: list[tuple[str, str]] = []
    for item in order_hints:
        if isinstance(item, dict) and item.get("company"):
            priority_keys.append(_experience_key(item["company"], item.get("role", "")))

    merged = _merge_tailored_with_profile(entries, profile)
    if not priority_keys:
        return merged

    def sort_key(entry: TailoredExperienceEntry) -> tuple[int, int]:
        key = _experience_key(entry.company, entry.role)
        for idx, pk in enumerate(priority_keys):
            if key == pk or key[0] == pk[0]:
                return idx, 0
        return len(priority_keys), 0

    return sorted(merged, key=sort_key)


async def _tailor_single_role(
    exp: Experience,
    jd_block: str,
    keywords: list[str],
    match_block: str,
    plan: dict,
) -> TailoredExperienceEntry:
    bullets_block = "\n".join(
        f"  {i}. {b}" for i, b in enumerate(exp.description[:MAX_EXPERIENCE_BULLETS], 1) if b.strip()
    )
    keyword_line = ", ".join(keywords[:12])
    user_msg = (
        f"TAILORING PLAN:\n{plan}\n\n"
        f"MATCH:\n{match_block}\n\n"
        f"ATS KEYWORDS: {keyword_line}\n\n"
        f"{jd_block}\n\n"
        f"ROLE TO REWRITE:\n"
        f"Company: {exp.company}\nRole: {exp.role}\nDuration: {exp.duration}\n"
        f"Original bullets ({len(exp.description)} total — output EXACTLY this many):\n{bullets_block}"
    )
    result = await chat_json(_ROLE_SYSTEM, user_msg, temperature=0.35, agent="resume_step2_experience")
    bullets = _ensure_bullet_count(
        sanitize_ai_string_list(result.get("bullets"), max_items=MAX_EXPERIENCE_BULLETS),
        exp.description,
    )
    return TailoredExperienceEntry(
        company=exp.company,
        role=exp.role,
        duration=exp.duration,
        bullets=bullets,
    )


async def run_resume_pipeline(
    profile: CandidateProfile,
    job_description: str,
    style: Optional[ResumeStyle] = None,
    match: Optional[MatchContextInput] = None,
    original: Optional[ResumeSnapshot] = None,
) -> ResumePreviewResponse:
    sorted_skills = sorted(profile.skills, key=lambda s: s.confidence, reverse=True)
    skill_names = [s.name for s in sorted_skills]
    profile_ctx = build_profile_context(profile, include_confidence=False)
    jd_block = wrap_untrusted_content("job_description", job_description)
    match_block = _match_context_block(match)
    original_block = _build_original_resume_block(original)

    style_ctx = ""
    if style:
        style_ctx = (
            f"\nReference style — tone: {sanitize_ai_text(style.tone, 120)}; "
            f"section order: {', '.join(style.section_order)}; "
            f"notes: {sanitize_ai_text(style.notes, 300)}"
        )

    raw_text = original.raw_text if original else ""

    # ── Step 0 (parallel): structure + ATS keywords ─────────────────────────
    structure_task = analyze_resume_structure(profile, raw_text)
    ats_task = extract_ats_keywords(job_description, match)
    structure, ats = await asyncio.gather(structure_task, ats_task)

    section_order = resolve_section_order(
        structure.get("section_order", []),
        style,
        original,
    )
    ats_keywords = ats.get("all_keywords") or sanitize_ai_string_list(
        (ats.get("primary_keywords") or []) + (ats.get("secondary_keywords") or [])
    )

    all_steps = _parse_steps(structure.get("tailoring_steps")) + _parse_steps(ats.get("tailoring_steps"))

    # ── Step 1: Tailoring plan ──────────────────────────────────────────────
    plan = await chat_json(
        _STEP1_SYSTEM,
        (
            f"RESUME STRUCTURE:\n{structure}\n\n"
            f"ATS KEYWORDS:\n{ats}\n\n"
            f"MATCH ANALYSIS:\n{match_block}\n\n"
            f"{original_block}\n\n"
            f"{jd_block}\n\n"
            f"CANDIDATE:\n{profile_ctx}{style_ctx}"
        ),
        temperature=0.3,
        agent="resume_step1_plan",
    )
    all_steps.extend(_parse_steps(plan.get("tailoring_steps")))

    keywords_to_weave = sanitize_ai_string_list(
        plan.get("keywords_to_weave") or ats_keywords, max_items=15,
    )
    shared_ctx = (
        f"TAILORING PLAN:\n{plan}\n\n"
        f"ATS KEYWORDS: {', '.join(keywords_to_weave)}\n\n"
        f"MATCH:\n{match_block}\n\n"
        f"{jd_block}\n\n"
        f"CANDIDATE:\n{profile_ctx}"
    )

    # ── Step 2 (parallel): summary, skills, experience roles, projects ─────
    summary_task = chat_json(
        _SUMMARY_SYSTEM,
        shared_ctx + f"\n\nOriginal summary:\n{profile.summary}",
        temperature=0.35,
        agent="resume_step2_summary",
    )
    skills_task = chat_json(
        _SKILLS_SYSTEM,
        shared_ctx + f"\n\nAll skills: {', '.join(skill_names)}",
        temperature=0.25,
        agent="resume_step2_skills",
    )
    projects_task = chat_json(
        _PROJECTS_SYSTEM,
        shared_ctx + f"\n\n{_build_original_experience_block(profile)}",
        temperature=0.3,
        agent="resume_step2_projects",
    )
    role_tasks = [
        _tailor_single_role(exp, jd_block, keywords_to_weave, match_block, plan)
        for exp in profile.experience[:25]
    ]

    summary_result, skills_result, projects_result, *role_results = await asyncio.gather(
        summary_task,
        skills_task,
        projects_task,
        *role_tasks,
        return_exceptions=True,
    )

    def _safe_dict(result: object, fallback: dict | None = None) -> dict:
        if isinstance(result, dict):
            return result
        return fallback or {}

    summary_data = _safe_dict(summary_result)
    skills_data = _safe_dict(skills_result)
    projects_data = _safe_dict(projects_result)

    tailored_roles: list[TailoredExperienceEntry] = []
    for i, result in enumerate(role_results):
        if isinstance(result, TailoredExperienceEntry):
            tailored_roles.append(result)
        elif i < len(profile.experience):
            exp = profile.experience[i]
            tailored_roles.append(
                TailoredExperienceEntry(
                    company=exp.company,
                    role=exp.role,
                    duration=exp.duration,
                    bullets=_ensure_bullet_count(exp.description, exp.description),
                )
            )

    for data in (summary_data, skills_data, projects_data):
        all_steps.extend(_parse_steps(data.get("tailoring_steps")))

    ordered = sanitize_ai_string_list(skills_data.get("ordered_skills")) or skill_names
    seen = {s.lower() for s in ordered}
    ordered += [s for s in skill_names if s.lower() not in seen]

    summary = scrub_forbidden_phrases(
        sanitize_ai_text(summary_data.get("tailored_summary", profile.summary), max_len=800)
    )

    tailored_experience = _order_experience_entries(tailored_roles, plan, profile)

    package = ResumePreviewResponse(
        tailored_summary=summary or profile.summary,
        ordered_skills=ordered,
        highlighted_projects=sanitize_ai_string_list(
            projects_data.get("highlighted_projects") or plan.get("priority_projects")
        ),
        key_achievements=sanitize_ai_string_list(projects_data.get("key_achievements")),
        emphasis=scrub_forbidden_phrases(
            sanitize_ai_text(projects_data.get("emphasis", ""), max_len=300)
        ),
        tailored_experience=tailored_experience,
        tailoring_steps=all_steps,
        section_order=section_order,
        ats_keywords=ats_keywords,
    )

    accent = style.accent_hex if style else "#10b981"
    package.latex_source = build_latex_document(
        profile, package, original=original, accent_hex=accent,
    )

    all_steps.append(
        MatchStep(
            step=len(all_steps) + 1,
            title="Generate LaTeX source",
            summary="Built structure-faithful LaTeX document from tailored content.",
        )
    )
    package.tailoring_steps = all_steps

    return package
