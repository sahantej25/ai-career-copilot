from models.schemas import CandidateProfile, Education, Experience, Project, Skill
from services.pdf_service import _safe_accent, generate_resume_pdf


def _sample_profile() -> CandidateProfile:
    return CandidateProfile(
        name="Jane Doe",
        email="jane@example.com",
        phone="555-0100",
        location="San Francisco, CA",
        summary="Experienced engineer.",
        skills=[
            Skill(name="React", confidence=90),
            Skill(name="Python", confidence=85),
        ],
        projects=[
            Project(name="Copilot", description="AI assistant", technologies=["React"]),
        ],
        experience=[
            Experience(
                company="Tech Corp",
                role="Senior Engineer",
                duration="2020 – Present",
                description=["Shipped major features"],
            )
        ],
        education=[
            Education(degree="B.S. CS", institution="State U", year="2016"),
        ],
    )


def test_safe_accent_valid_hex():
    color = _safe_accent("#10b981")
    assert color.hexval() == "0x10b981"


def test_safe_accent_invalid_hex_falls_back():
    color = _safe_accent("not-a-color")
    assert color.hexval() == "0x10b981"


def test_generate_resume_pdf_returns_bytes():
    pdf_bytes = generate_resume_pdf(
        profile=_sample_profile(),
        tailored_summary="Full-stack engineer specializing in React and Python.",
        ordered_skills=["React", "Python", "TypeScript"],
        highlighted_projects=["Copilot"],
        section_order=["summary", "skills", "experience", "projects", "education"],
        accent_hex="#10b981",
    )
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes[:4] == b"%PDF"
    assert len(pdf_bytes) > 500
