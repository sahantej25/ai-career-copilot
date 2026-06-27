import io
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, ListFlowable, ListItem
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER

from models.schemas import CandidateProfile


# Colour palette
DARK = colors.HexColor("#1E293B")
ACCENT = colors.HexColor("#4F46E5")
MID = colors.HexColor("#475569")
LIGHT = colors.HexColor("#F8FAFC")
WHITE = colors.white


def _styles():
    base = getSampleStyleSheet()
    return {
        "name": ParagraphStyle("name", fontSize=22, textColor=DARK, fontName="Helvetica-Bold",
                                spaceAfter=2, alignment=TA_LEFT),
        "contact": ParagraphStyle("contact", fontSize=9, textColor=MID, fontName="Helvetica",
                                   spaceAfter=6, alignment=TA_LEFT),
        "section": ParagraphStyle("section", fontSize=11, textColor=ACCENT,
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


def generate_resume_pdf(profile: CandidateProfile, tailored_summary: str,
                         ordered_skills: list[str]) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        leftMargin=0.65 * inch,
        rightMargin=0.65 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
    )
    s = _styles()
    story = []

    # ── Header ──────────────────────────────────────────────────────────────
    story.append(Paragraph(profile.name or "Candidate", s["name"]))
    contact_parts = [x for x in [profile.email, profile.phone, profile.location] if x]
    if contact_parts:
        story.append(Paragraph("  |  ".join(contact_parts), s["contact"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceAfter=6))

    # ── Summary ─────────────────────────────────────────────────────────────
    if tailored_summary:
        story.append(Paragraph("PROFESSIONAL SUMMARY", s["section"]))
        story.append(Paragraph(tailored_summary, s["body"]))

    # ── Skills ───────────────────────────────────────────────────────────────
    if ordered_skills:
        story.append(Paragraph("TECHNICAL SKILLS", s["section"]))
        chunks = [ordered_skills[i:i+4] for i in range(0, len(ordered_skills), 4)]
        for chunk in chunks:
            story.append(Paragraph("  •  ".join(chunk), s["body"]))

    # ── Experience ───────────────────────────────────────────────────────────
    if profile.experience:
        story.append(Paragraph("EXPERIENCE", s["section"]))
        for exp in profile.experience:
            story.append(Paragraph(exp.role, s["job_title"]))
            story.append(Paragraph(f"{exp.company}  —  {exp.duration}", s["company"]))
            for bullet in exp.description[:4]:
                story.append(Paragraph(f"• {bullet}", s["bullet"]))
            story.append(Spacer(1, 4))

    # ── Projects ─────────────────────────────────────────────────────────────
    if profile.projects:
        story.append(Paragraph("PROJECTS", s["section"]))
        for proj in profile.projects[:4]:
            tech_str = ", ".join(proj.technologies) if proj.technologies else ""
            title = f"{proj.name}" + (f"  [{tech_str}]" if tech_str else "")
            story.append(Paragraph(title, s["job_title"]))
            story.append(Paragraph(proj.description, s["bullet"]))
            story.append(Spacer(1, 4))

    # ── Education ────────────────────────────────────────────────────────────
    if profile.education:
        story.append(Paragraph("EDUCATION", s["section"]))
        for edu in profile.education:
            story.append(Paragraph(edu.degree, s["job_title"]))
            story.append(Paragraph(f"{edu.institution}  —  {edu.year}", s["company"]))

    doc.build(story)
    return buffer.getvalue()
