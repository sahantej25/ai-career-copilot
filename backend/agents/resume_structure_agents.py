"""Parallel resume structure + ATS keyword agents (step 0 of tailoring pipeline)."""
import re
from typing import Optional

from models.schemas import CandidateProfile, MatchContextInput, ResumeSnapshot, ResumeStyle
from services.guardrails import (
    sanitize_ai_string_list,
    sanitize_ai_text,
    validate_section_order,
    wrap_untrusted_content,
)
from services.openai_service import chat_json

_STRUCTURE_SYSTEM = """You analyze a candidate's ORIGINAL resume text and structured profile.
Extract the document structure — do NOT rewrite content.

Return ONLY valid JSON:
{
  "section_order": ["summary","skills","experience","projects","education"],
  "sections_found": ["list of section headings detected in the original"],
  "structure_notes": "1 sentence on layout (e.g. reverse-chronological experience, skills grid)",
  "tailoring_steps": [
    {"step": 1, "title": "Map original structure", "summary": "1 sentence"}
  ]
}
section_order must only use: summary, skills, experience, projects, education.
Preserve the order sections appear in the original resume when possible."""

_ATS_SYSTEM = """You extract ATS-relevant keywords from a job description for resume optimization.
Return ONLY valid JSON:
{
  "primary_keywords": ["8-12 must-have JD terms for ATS"],
  "secondary_keywords": ["5-8 nice-to-have terms"],
  "role_titles": ["how the JD titles this role"],
  "tailoring_steps": [
    {"step": 1, "title": "Extract ATS keywords", "summary": "1 sentence"}
  ]
}
Use exact phrases from the JD where possible. Do not invent requirements."""

_SECTION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("summary", re.compile(r"\b(professional\s+summary|summary|profile|objective)\b", re.I)),
    ("skills", re.compile(r"\b(skills|technical\s+skills|core\s+competencies|expertise)\b", re.I)),
    ("experience", re.compile(r"\b(experience|work\s+history|employment|professional\s+experience)\b", re.I)),
    ("projects", re.compile(r"\b(projects|personal\s+projects|selected\s+projects)\b", re.I)),
    ("education", re.compile(r"\b(education|academic|qualifications)\b", re.I)),
]


def infer_section_order_heuristic(raw_text: str) -> list[str]:
    """Detect section order from headings in raw resume text."""
    if not raw_text.strip():
        return validate_section_order([])
    positions: list[tuple[int, str]] = []
    for section_id, pattern in _SECTION_PATTERNS:
        match = pattern.search(raw_text)
        if match:
            positions.append((match.start(), section_id))
    positions.sort(key=lambda x: x[0])
    order = [sec for _, sec in positions]
    return validate_section_order(order)


def resolve_section_order(
    structure_order: list[str],
    style: Optional[ResumeStyle],
    snapshot: Optional[ResumeSnapshot],
) -> list[str]:
    """Pick the best section order: AI structure > reference style > upload heuristic."""
    if structure_order:
        return validate_section_order(structure_order)
    if style and style.section_order:
        return validate_section_order(style.section_order)
    if snapshot and snapshot.section_order:
        return validate_section_order(snapshot.section_order)
    return validate_section_order([])


async def analyze_resume_structure(
    profile: CandidateProfile,
    raw_text: str = "",
) -> dict:
    heuristic = infer_section_order_heuristic(raw_text)
    if not raw_text.strip():
        return {
            "section_order": heuristic,
            "sections_found": [],
            "structure_notes": "Inferred from structured profile.",
            "tailoring_steps": [],
        }

    from agents.shared.profile_context import build_profile_context

    profile_ctx = build_profile_context(profile, include_confidence=False)
    resume_block = wrap_untrusted_content("original_resume", raw_text[:8000])
    result = await chat_json(
        _STRUCTURE_SYSTEM,
        f"{resume_block}\n\nSTRUCTURED PROFILE (for cross-check):\n{profile_ctx}",
        temperature=0.2,
        agent="resume_step0_structure",
    )
    order = validate_section_order(result.get("section_order")) or heuristic
    result["section_order"] = order
    return result


async def extract_ats_keywords(
    job_description: str,
    match: Optional[MatchContextInput] = None,
) -> dict:
    jd_block = wrap_untrusted_content("job_description", job_description)
    match_lines = []
    if match:
        match_lines = [
            f"Match score: {match.match_percentage:.0f}%",
            f"Matched: {', '.join(match.matched_skills[:15])}",
            f"Missing: {', '.join(match.missing_skills[:15])}",
        ]
    match_block = "\n".join(match_lines) if match_lines else "No prior match analysis."

    result = await chat_json(
        _ATS_SYSTEM,
        f"MATCH CONTEXT:\n{match_block}\n\n{jd_block}",
        temperature=0.2,
        agent="resume_step0_ats",
    )
    primary = sanitize_ai_string_list(result.get("primary_keywords"), max_items=15)
    secondary = sanitize_ai_string_list(result.get("secondary_keywords"), max_items=10)
    result["primary_keywords"] = primary
    result["secondary_keywords"] = secondary
    result["all_keywords"] = primary + [k for k in secondary if k.lower() not in {p.lower() for p in primary}]
    return result
