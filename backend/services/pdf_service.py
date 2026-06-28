import io
from typing import Optional

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_LEFT

from models.schemas import CandidateProfile, TailoredExperienceEntry
from services.guardrails.constants import MAX_EXPERIENCE_BULLETS


DARK = colors.HexColor("#1E293B")
MID = colors.HexColor("#475569")

DEFAULT_SECTION_ORDER = ["summary", "skills", "experience", "projects", "education"]


def _styles(accent: colors.Color):
    return {
        "name": ParagraphStyle("name", fontSize=22, textColor=DARK, fontName="Helvetica-Bold",
                               spaceAfter=2, alignment=TA_LEFT),
        "contact": ParagraphStyle("contact", fontSize=9, textColor=MID, fontName="Helvetica",
                                  spaceAfter=6, alignment=TA_LEFT),
        "section": ParagraphStyle("section", fontSize=11, textColor=accent,
                                  fontName="Helvetica-Bold", spaceBefore=12, spaceAfter=4),
        "body": ParagraphStyle("body", fontSize=9.5, textColor=DARK, fontName="Helvetica",
                               leading=14, spaceAfter=4),
        "bullet": ParagraphStyle("bullet", fontSize=9.5, textColor=DARK, fontName="Helvetica",
                                 leading=13, leftIndent=12, spaceAfter=2),
        "job_title": ParagraphStyle("job_title", fontSize=10, textColor=DARK,
                                    fontName="Helvetica-Bold", spaceAfter=1),
        "company": ParagraphStyle("company", fontSize=9.5, textColor=MID,
                                  fontName="Helvetica-Oblique", spaceAfter=3),
    }


def _safe_accent(accent_hex: str) -> colors.Color:
    try:
        return colors.HexColor(accent_hex)
    except Exception:
        return colors.HexColor("#10b981")


def generate_resume_pdf(
    profile: CandidateProfile,
    tailored_summary: str,
    ordered_skills: list[str],
    highlighted_projects: Optional[list[str]] = None,
    tailored_experience: Optional[list[TailoredExperienceEntry]] = None,
    section_order: Optional[list[str]] = None,
    accent_hex: str = "#10b981",
) -> bytes:
    accent = _safe_accent(accent_hex)
    s = _styles(accent)
    highlighted = {p.lower() for p in (highlighted_projects or [])}
    order = [x for x in (section_order or DEFAULT_SECTION_ORDER) if x in DEFAULT_SECTION_ORDER]
    for sec in DEFAULT_SECTION_ORDER:
        if sec not in order:
            order.append(sec)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=LETTER,
        leftMargin=0.65 * inch, rightMargin=0.65 * inch,
        topMargin=0.65 * inch, bottomMargin=0.65 * inch,
    )
    story = []

    # ── Header (always first) ────────────────────────────────────────────────
    story.append(Paragraph(profile.name or "Candidate", s["name"]))
    contact_parts = [x for x in [profile.email, profile.phone, profile.location] if x]
    if contact_parts:
        story.append(Paragraph("  |  ".join(contact_parts), s["contact"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=accent, spaceAfter=6))

    def render_summary():
        if tailored_summary:
            story.append(Paragraph("PROFESSIONAL SUMMARY", s["section"]))
            story.append(Paragraph(tailored_summary, s["body"]))

    def render_skills():
        if ordered_skills:
            # The most JD-relevant skills lead — mirrors "Skills Relevant to This Role".
            story.append(Paragraph("SKILLS RELEVANT TO THIS ROLE", s["section"]))
            chunks = [ordered_skills[i:i + 4] for i in range(0, len(ordered_skills), 4)]
            for chunk in chunks:
                story.append(Paragraph("  •  ".join(chunk), s["body"]))

    def render_experience():
        exp_entries = tailored_experience
        if not exp_entries and profile.experience:
            exp_entries = [
                TailoredExperienceEntry(
                    company=exp.company,
                    role=exp.role,
                    duration=exp.duration,
                    bullets=exp.description[:MAX_EXPERIENCE_BULLETS],
                )
                for exp in profile.experience
            ]
        if exp_entries:
            story.append(Paragraph("EXPERIENCE", s["section"]))
            for exp in exp_entries:
                story.append(Paragraph(exp.role, s["job_title"]))
                story.append(Paragraph(f"{exp.company}  —  {exp.duration}", s["company"]))
                for bullet in exp.bullets[:MAX_EXPERIENCE_BULLETS]:
                    story.append(Paragraph(f"• {bullet}", s["bullet"]))
                story.append(Spacer(1, 4))

    def render_projects():
        if profile.projects:
            story.append(Paragraph("PROJECTS", s["section"]))
            # Surface highlighted (JD-relevant) projects first.
            ordered_projects = sorted(
                profile.projects,
                key=lambda p: 0 if p.name.lower() in highlighted else 1,
            )
            for proj in ordered_projects[:5]:
                tech = ", ".join(proj.technologies) if proj.technologies else ""
                title = proj.name + (f"  [{tech}]" if tech else "")
                story.append(Paragraph(title, s["job_title"]))
                if proj.description:
                    story.append(Paragraph(proj.description, s["bullet"]))
                story.append(Spacer(1, 4))

    def render_education():
        if profile.education:
            story.append(Paragraph("EDUCATION", s["section"]))
            for edu in profile.education:
                story.append(Paragraph(edu.degree, s["job_title"]))
                story.append(Paragraph(f"{edu.institution}  —  {edu.year}", s["company"]))

    renderers = {
        "summary": render_summary,
        "skills": render_skills,
        "experience": render_experience,
        "projects": render_projects,
        "education": render_education,
    }
    for sec in order:
        renderers[sec]()

    doc.build(story)
    return buffer.getvalue()
