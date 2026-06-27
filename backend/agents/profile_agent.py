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

from services.openai_service import chat_json
from models.schemas import CandidateProfile, Skill, Project, Experience, Education


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
        # Try as plain text
        return file_bytes.decode("utf-8", errors="ignore")


async def parse_resume(file_bytes: bytes, filename: str) -> CandidateProfile:
    raw_text = extract_text(file_bytes, filename)
    if not raw_text.strip():
        raise ValueError("Could not extract text from the uploaded file.")

    data = await chat_json(_SYSTEM, f"Resume text:\n\n{raw_text[:8000]}")

    skills = [
        Skill(
            name=s.get("name", ""),
            confidence=float(s.get("confidence", 70)),
            category=s.get("category", "general"),
        )
        for s in data.get("skills", [])
        if s.get("name")
    ]
    projects = [
        Project(
            name=p.get("name", ""),
            description=p.get("description", ""),
            technologies=p.get("technologies", []),
        )
        for p in data.get("projects", [])
    ]
    experience = [
        Experience(
            company=e.get("company", ""),
            role=e.get("role", ""),
            duration=e.get("duration", ""),
            description=e.get("description", []),
        )
        for e in data.get("experience", [])
    ]
    education = [
        Education(
            degree=e.get("degree", ""),
            institution=e.get("institution", ""),
            year=e.get("year", ""),
        )
        for e in data.get("education", [])
    ]

    return CandidateProfile(
        name=data.get("name", ""),
        email=data.get("email", ""),
        phone=data.get("phone", ""),
        location=data.get("location", ""),
        summary=data.get("summary", ""),
        skills=skills,
        projects=projects,
        experience=experience,
        education=education,
        domains=data.get("domains", []),
    )
