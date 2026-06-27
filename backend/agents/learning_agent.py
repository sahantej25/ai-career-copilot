"""Agent 4 – Learning & Insights Agent (the most important AI component)
Analyzes rejection notes → updates profile confidence → generates global insights.
"""
from datetime import datetime

from models.schemas import (
    CandidateProfile, RejectionNote, Application,
    ProfileUpdate, SkillChange, GlobalAnalysis, RadarDataPoint, AppData,
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
"""

_GLOBAL_SYSTEM = """You are a career strategist analyzing patterns across multiple job rejections.
Given a list of rejections with their skill gaps and recommendations, identify macro patterns.
Return ONLY valid JSON:
{
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
) -> tuple[ProfileUpdate, CandidateProfile]:
    """Returns (ProfileUpdate, updated CandidateProfile)."""
    skill_snapshot = [
        {"name": s.name, "confidence": s.confidence, "category": s.category}
        for s in profile.skills
    ]
    ctx = (
        f"Company: {application.company}\n"
        f"Role: {application.role}\n"
        f"Match was: {application.match_percentage:.0f}%\n"
        f"Missing skills identified at apply-time: {', '.join(application.missing_skills)}\n\n"
        f"Current skill profile:\n{skill_snapshot}\n\n"
        f"Rejection feedback:\n"
        f"Interview experience: {rejection.interview_experience}\n"
        f"Rejection email: {rejection.rejection_email}\n"
        f"Topics struggled: {rejection.topics_struggled}\n"
        f"Missing skills (candidate noted): {rejection.missing_skills}\n"
        f"Recruiter feedback: {rejection.recruiter_feedback}"
    )

    data = await chat_json(_REJECTION_SYSTEM, ctx)

    skill_changes: list[SkillChange] = []
    skill_map = {s.name.lower(): s for s in profile.skills}

    for change in data.get("skill_changes", []):
        sname = change.get("skill", "")
        delta = float(change.get("confidence_delta", 0))
        key = sname.lower()
        if key in skill_map:
            skill = skill_map[key]
            prev = skill.confidence
            skill.confidence = max(0, min(100, prev + delta))
            skill_changes.append(SkillChange(
                skill=sname,
                previous_confidence=prev,
                new_confidence=skill.confidence,
                reason=change.get("reason", ""),
            ))

    # Add newly discovered skills
    for ns in data.get("new_skills_to_add", []):
        from models.schemas import Skill
        if ns.get("name", "").lower() not in skill_map:
            profile.skills.append(Skill(
                name=ns["name"],
                confidence=float(ns.get("confidence", 30)),
                category=ns.get("category", "general"),
            ))

    update = ProfileUpdate(
        triggered_by=application.id,
        company=application.company,
        changes=skill_changes,
        recommendations=data.get("recommendations", []),
    )

    return update, profile


async def build_global_analysis(data: AppData) -> GlobalAnalysis:
    """Aggregate patterns from all rejections and profile history."""
    if not data.rejections:
        return GlobalAnalysis()

    rejection_summaries = []
    for rej in data.rejections:
        app = next((a for a in data.applications if a.id == rej.application_id), None)
        if app:
            rejection_summaries.append(
                f"Company: {app.company} | Role: {app.role} | "
                f"Missing skills: {', '.join(app.missing_skills)} | "
                f"Topics struggled: {rej.topics_struggled} | "
                f"Recruiter feedback: {rej.recruiter_feedback}"
            )

    history_recs = [
        rec
        for upd in data.profile_update_history
        for rec in upd.recommendations
    ]

    ctx = (
        f"Total applications: {len(data.applications)}\n"
        f"Total rejections analyzed: {len(data.rejections)}\n\n"
        f"Rejection details:\n" + "\n".join(rejection_summaries) +
        f"\n\nPast recommendations given:\n" + "\n".join(history_recs[:20])
    )
    if data.current_profile_state:
        profile_skills = [
            {"category": s.category, "confidence": s.confidence}
            for s in data.current_profile_state.skills
        ]
        ctx += f"\n\nCurrent skill profile: {profile_skills}"

    result = await chat_json(_GLOBAL_SYSTEM, ctx, temperature=0.3)

    radar = [
        RadarDataPoint(
            subject=r.get("subject", ""),
            value=float(r.get("value", 50)),
            full_mark=float(r.get("full_mark", 100)),
        )
        for r in result.get("skill_radar_data", [])
    ]

    return GlobalAnalysis(
        recurring_missing_skills=result.get("recurring_missing_skills", []),
        common_interview_topics=result.get("common_interview_topics", []),
        frequent_weaknesses=result.get("frequent_weaknesses", []),
        career_recommendations=result.get("career_recommendations", []),
        skill_radar_data=radar,
    )
