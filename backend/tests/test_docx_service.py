"""Tests for structured DOCX resume export."""
from models.schemas import CandidateProfile, ResumePreviewResponse, TailoredExperienceEntry
from services.docx_service import generate_docx_from_package


def test_generate_docx_from_package_returns_docx_bytes():
    profile = CandidateProfile(
        name="Jane Doe",
        email="jane@example.com",
        summary="Engineer",
    )
    package = ResumePreviewResponse(
        tailored_summary="Tailored summary for role.",
        ordered_skills=["React", "Python"],
        tailored_experience=[
            TailoredExperienceEntry(
                company="Acme",
                role="Engineer",
                duration="2020 – Present",
                bullets=["Shipped features"],
            )
        ],
        section_order=["summary", "skills", "experience"],
    )
    docx_bytes = generate_docx_from_package(profile, package)
    assert docx_bytes[:2] == b"PK"
