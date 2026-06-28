"""Agent 1 – Profile Intelligence Agent
Parses raw resume text → structured CandidateProfile.
"""
import io
from typing import Optional

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None

from services.guardrails import (
    clamp_percentage,
    sanitize_ai_text,
    sanitize_name,
    validate_hex_color,
    validate_section_order,
    wrap_untrusted_content,
)
from services.guardrails.constants import MAX_EXPERIENCE_BULLETS, MAX_REFERENCE_TEXT_CHARS, MAX_RESUME_TEXT_CHARS, MAX_SKILLS
from services.openai_service import chat_json
from models.schemas import CandidateProfile, Skill, Project, Experience, Education, ResumeStyle


_SYSTEM = """You are a resume parser. Extract structured information from the given resume text.
Return ONLY valid JSON with this exact schema:
{
  "name": "string",
  "email": "string",
  "phone": "string",
  "location": "string",
  "summary": "string (2-3 sentences)",
  "skills": [{"name": "string", "confidence": 75, "category": "string"}],
  "projects": [{"name": "string", "description": "string", "technologies": ["string"]}],
  "experience": [{"company": "string", "role": "string", "duration": "string", "description": ["bullet"]}],
  "education": [{"degree": "string", "institution": "string", "year": "string"}],
  "domains": ["string"]
}
Confidence is 0-100 based on how prominently the skill appears. Category is one of:
programming, framework, database, cloud, tool, soft-skill, domain, other.
Do not invent credentials, employers, or skills not present in the resume text.
Extract EVERY bullet point under each role — do not summarize, merge, or drop bullets.
Preserve the original resume section structure and ordering.
"""


def extract_text_from_pdf(file_bytes: bytes) -> str:
    if PyPDF2 is None:
        return ""
    reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def extract_text_from_docx(file_bytes: bytes) -> str:
    if DocxDocument is None:
        return ""
    doc = DocxDocument(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in doc.paragraphs)


def extract_text(file_bytes: bytes, filename: str) -> str:
    ext = filename.lower().rsplit(".", 1)[-1]
    if ext == "pdf":
        return extract_text_from_pdf(file_bytes)
    elif ext in ("docx", "doc"):
        return extract_text_from_docx(file_bytes)
    else:
        return file_bytes.decode("utf-8", errors="ignore")


async def parse_resume(file_bytes: bytes, filename: str) -> CandidateProfile:
    raw_text = extract_text(file_bytes, filename)
    if not raw_text.strip():
        raise ValueError("Could not extract text from the uploaded file.")

    resume_block = wrap_untrusted_content(
        "resume_text",
        raw_text[:MAX_RESUME_TEXT_CHARS],
        max_len=MAX_RESUME_TEXT_CHARS,
    )
    data = await chat_json(_SYSTEM, resume_block, agent="profile_parser")

    skills = [
        Skill(
            name=sanitize_ai_text(s.get("name", ""), max_len=80),
            confidence=clamp_percentage(s.get("confidence", 70), default=70),
            category=sanitize_ai_text(s.get("category", "general"), max_len=40) or "general",
        )
        for s in data.get("skills", [])[:MAX_SKILLS]
        if s.get("name")
    ]
    projects = [
        Project(
            name=sanitize_ai_text(p.get("name", ""), max_len=120),
            description=sanitize_ai_text(p.get("description", ""), max_len=500),
            technologies=[
                sanitize_ai_text(t, max_len=60)
                for t in (p.get("technologies") or [])[:20]
                if t
            ],
        )
        for p in data.get("projects", [])[:30]
    ]
    experience = [
        Experience(
            company=sanitize_ai_text(e.get("company", ""), max_len=120),
            role=sanitize_ai_text(e.get("role", ""), max_len=120),
            duration=sanitize_ai_text(e.get("duration", ""), max_len=80),
            description=[
                sanitize_ai_text(b, max_len=400)
                for b in (e.get("description") or [])[:MAX_EXPERIENCE_BULLETS]
                if b
            ],
        )
        for e in data.get("experience", [])[:25]
    ]
    education = [
        Education(
            degree=sanitize_ai_text(e.get("degree", ""), max_len=120),
            institution=sanitize_ai_text(e.get("institution", ""), max_len=120),
            year=sanitize_ai_text(e.get("year", ""), max_len=20),
        )
        for e in data.get("education", [])[:10]
    ]

    return CandidateProfile(
        name=sanitize_name(data.get("name", "")),
        email=sanitize_ai_text(data.get("email", ""), max_len=120),
        phone=sanitize_ai_text(data.get("phone", ""), max_len=40),
        location=sanitize_ai_text(data.get("location", ""), max_len=120),
        summary=sanitize_ai_text(data.get("summary", ""), max_len=800),
        skills=skills,
        projects=projects,
        experience=experience,
        education=education,
        domains=[
            sanitize_ai_text(d, max_len=60)
            for d in data.get("domains", [])[:20]
            if d
        ],
    )


_STYLE_SYSTEM = """You analyze a reference resume purely for its STYLE and STRUCTURE.
Do NOT copy any content. Identify how it is organized and presented.
Return ONLY valid JSON:
{
  "section_order": ["summary","skills","experience","projects","education"],
  "tone": "short phrase, e.g. 'concise & impact-driven' or 'detailed & academic'",
  "accent_hex": "a hex color that fits the resume's vibe, e.g. #10b981",
  "notes": "1-2 sentences on layout/formatting characteristics to emulate"
}
section_order must only use values from: summary, skills, experience, projects, education.
"""


async def extract_resume_style(file_bytes: bytes, filename: str) -> ResumeStyle:
    """Parse an optional reference resume and infer stylistic guidance only."""
    raw_text = extract_text(file_bytes, filename)
    if not raw_text.strip():
        raise ValueError("Could not extract text from the reference resume.")

    resume_block = wrap_untrusted_content(
        "reference_resume",
        raw_text[:MAX_REFERENCE_TEXT_CHARS],
        max_len=MAX_REFERENCE_TEXT_CHARS,
    )
    data = await chat_json(_STYLE_SYSTEM, resume_block, agent="resume_style")

    return ResumeStyle(
        section_order=validate_section_order(data.get("section_order")),
        tone=sanitize_ai_text(data.get("tone", ""), max_len=120),
        accent_hex=validate_hex_color(data.get("accent_hex")),
        notes=sanitize_ai_text(data.get("notes", ""), max_len=300),
    )
