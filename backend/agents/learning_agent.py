"""Agent 4 – Learning & Insights Agent (the most important AI component)
Analyzes rejection notes → updates profile confidence → generates global insights.
"""
from datetime import datetime

from models.schemas import (
    CandidateProfile, RejectionNote, Application, ApplicationStatus,
    ProfileUpdate, SkillChange, GlobalAnalysis, RadarDataPoint, AppData, Skill,
)
from services.guardrails import (
    clamp_confidence_delta,
    clamp_percentage,
    sanitize_ai_string_list,
    sanitize_ai_text,
    wrap_untrusted_content,
)
from services.openai_service import chat_json


_REJECTION_SYSTEM = """You are a career coach analyzing a job application rejection.
Given the candidate's current skill profile and rejection feedback, produce actionable insights.
Return ONLY valid JSON:
{
  "skill_changes": [
    {"skill": "Docker", "confidence_delta": -15, "reason": "Struggled with container orchestration questions"}
  ],
  "new_skills_to_add": [
    {"name": "Kubernetes", "confidence": 30, "category": "cloud"}
  ],
  "recommendations": ["Learn Docker Compose", "Build a Kubernetes side project"],
  "summary": "2-3 sentence summary of what this rejection reveals."
}
confidence_delta is negative for weaknesses revealed, positive if candidate demonstrated strength.
Keep changes realistic: -5 to -30 for weaknesses, +5 to +15 for strengths.
Base skill changes ONLY on evidence in the rejection feedback — do not speculate wildly.
"""


_GLOBAL_SYSTEM = """You are a career strategist analyzing patterns across multiple job rejections.
Given a list of rejections with their skill gaps and recommendations, identify macro patterns.
Return ONLY valid JSON:
{
  "summary": "A plain-language paragraph (3-5 sentences) telling the candidate what to focus on improving before their next round of applications.",
  "recurring_missing_skills": ["Docker", "System Design"],
  "common_interview_topics": ["Behavioral questions", "System design"],
  "frequent_weaknesses": ["Distributed systems", "Cloud infrastructure"],
  "career_recommendations": [
    "Invest 4-6 weeks in container technologies",
    "Complete a system design course"
  ],
  "skill_radar_data": [
    {"subject": "Programming", "value": 85, "full_mark": 100},
    {"subject": "Cloud", "value": 45, "full_mark": 100},
    {"subject": "Databases", "value": 70, "full_mark": 100},
    {"subject": "DevOps", "value": 40, "full_mark": 100},
    {"subject": "Frontend", "value": 65, "full_mark": 100},
    {"subject": "System Design", "value": 50, "full_mark": 100}
  ]
}
"""


async def analyze_rejection(
    profile: CandidateProfile,
    rejection: RejectionNote,
    application: Application,
) -> tuple[ProfileUpdate, CandidateProfile, str]:
    """Returns (ProfileUpdate, updated CandidateProfile, summary)."""
    skill_snapshot = [
        {"name": s.name, "confidence": s.confidence, "category": s.category}
        for s in profile.skills
    ]
    structured = "\n".join(
        f"{label}: {val}"
        for label, val in [
            ("Interview experience", rejection.interview_experience),
            ("Rejection email", rejection.rejection_email),
            ("Topics struggled", rejection.topics_struggled),
            ("Missing skills (candidate noted)", rejection.missing_skills),
            ("Recruiter feedback", rejection.recruiter_feedback),
        ]
        if val
    )
    ctx = (
        f"Company: {application.company}\n"
        f"Role: {application.role}\n"
        f"Match was: {application.match_percentage:.0f}%\n"
        f"Missing skills identified at apply-time: {', '.join(application.missing_skills)}\n\n"
        f"Current skill profile:\n{skill_snapshot}\n\n"
        f"Candidate's rejection notes (free text):\n{rejection.notes or '(none)'}\n\n"
        f"Additional structured details:\n{structured or '(none)'}"
    )

    notes_block = wrap_untrusted_content("rejection_feedback", ctx)
    data = await chat_json(_REJECTION_SYSTEM, notes_block, agent="rejection_analysis")

    skill_changes: list[SkillChange] = []
    skill_map = {s.name.lower(): s for s in profile.skills}

    for change in data.get("skill_changes", [])[:20]:
        sname = sanitize_ai_text(change.get("skill", ""), max_len=80)
        delta = clamp_confidence_delta(change.get("confidence_delta", 0))
        key = sname.lower()
        if key in skill_map:
            skill = skill_map[key]
            prev = skill.confidence
            skill.confidence = clamp_percentage(prev + delta)
            skill_changes.append(SkillChange(
                skill=sname,
                previous_confidence=prev,
                new_confidence=skill.confidence,
                reason=sanitize_ai_text(change.get("reason", ""), max_len=300),
            ))

    for ns in data.get("new_skills_to_add", [])[:10]:
        name = sanitize_ai_text(ns.get("name", ""), max_len=80)
        if name and name.lower() not in skill_map:
            profile.skills.append(Skill(
                name=name,
                confidence=clamp_percentage(ns.get("confidence", 30), default=30),
                category=sanitize_ai_text(ns.get("category", "general"), max_len=40) or "general",
            ))

    update = ProfileUpdate(
        triggered_by=application.id,
        company=application.company,
        changes=skill_changes,
        recommendations=sanitize_ai_string_list(data.get("recommendations")),
    )

    summary = sanitize_ai_text(data.get("summary", ""), max_len=600) or (
        f"Profile updated based on the rejection from {application.company}."
    )

    return update, profile, summary


def collect_rejection_summaries(data: AppData) -> list[str]:
    """Build analysis context from every not-selected application."""
    rejection_by_app = {r.application_id: r for r in data.rejections}
    summaries: list[str] = []
    for app in data.applications:
        if app.status != ApplicationStatus.not_selected:
            continue
        rej = rejection_by_app.get(app.id)
        summaries.append(
            f"Company: {app.company} | Role: {app.role} | "
            f"Match: {app.match_percentage:.0f}% | "
            f"Missing skills: {', '.join(app.missing_skills) or (rej.missing_skills if rej else '') or 'unknown'} | "
            f"Topics struggled: {(rej.topics_struggled if rej else '') or '(not specified)'} | "
            f"Recruiter feedback: {(rej.recruiter_feedback if rej else '') or '(not specified)'} | "
            f"Notes: {(rej.notes if rej else app.notes) or '(none)'}"
        )
    return summaries


async def build_global_analysis(data: AppData) -> GlobalAnalysis:
    """Aggregate patterns from all rejections and profile history."""
    rejection_summaries = collect_rejection_summaries(data)
    if not rejection_summaries:
        return GlobalAnalysis()

    history_recs = [
        rec
        for upd in data.profile_update_history
        for rec in upd.recommendations
    ]

    ctx = (
        f"Total applications: {len(data.applications)}\n"
        f"Total rejections: {len(rejection_summaries)}\n\n"
        f"Rejection details:\n" + "\n".join(rejection_summaries) +
        f"\n\nPast recommendations given:\n" + "\n".join(history_recs[:20])
    )
    if data.current_profile_state:
        profile_skills = [
            {"category": s.category, "confidence": s.confidence}
            for s in data.current_profile_state.skills
        ]
        ctx += f"\n\nCurrent skill profile: {profile_skills}"

    aggregate_block = wrap_untrusted_content("rejection_history", ctx)
    result = await chat_json(_GLOBAL_SYSTEM, aggregate_block, temperature=0.3, agent="global_analysis")

    radar = [
        RadarDataPoint(
            subject=sanitize_ai_text(r.get("subject", ""), max_len=60),
            value=clamp_percentage(r.get("value", 50), default=50),
            full_mark=clamp_percentage(r.get("full_mark", 100), default=100),
        )
        for r in result.get("skill_radar_data", [])[:12]
        if r.get("subject")
    ]

    return GlobalAnalysis(
        summary=sanitize_ai_text(result.get("summary", ""), max_len=1200),
        recurring_missing_skills=sanitize_ai_string_list(result.get("recurring_missing_skills")),
        common_interview_topics=sanitize_ai_string_list(result.get("common_interview_topics")),
        frequent_weaknesses=sanitize_ai_string_list(result.get("frequent_weaknesses")),
        career_recommendations=sanitize_ai_string_list(result.get("career_recommendations")),
        skill_radar_data=radar,
        last_updated=datetime.utcnow().isoformat() + "Z",
    )
