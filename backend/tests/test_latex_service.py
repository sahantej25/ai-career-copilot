"""Tests for LaTeX resume builder and sanitizer."""
from models.schemas import CandidateProfile, Experience, ResumePreviewResponse, TailoredExperienceEntry
from services.latex_service import (
    build_latex_document,
    compile_latex_to_pdf,
    escape_latex,
    generate_resume_pdf_from_package,
    sanitize_latex_source,
)


def _sample_package() -> ResumePreviewResponse:
    return ResumePreviewResponse(
        tailored_summary="Senior engineer with React expertise.",
        ordered_skills=["React", "Python"],
        tailored_experience=[
            TailoredExperienceEntry(
                company="Acme",
                role="Engineer",
                duration="2020 – Present",
                bullets=["Built dashboards for 50k users"],
            )
        ],
        section_order=["summary", "skills", "experience", "education"],
    )


def test_escape_latex_special_chars():
    assert r"\&" in escape_latex("A & B")
    assert r"\%" in escape_latex("100%")
    assert r"\_" in escape_latex("foo_bar")


def test_sanitize_latex_strips_dangerous_commands():
    dirty = r"\documentclass{article}\input{/etc/passwd}"
    cleaned = sanitize_latex_source(dirty)
    assert r"\input" not in cleaned


def test_build_latex_document_includes_sections():
    profile = CandidateProfile(
        name="Jane Doe",
        email="jane@example.com",
        experience=[
            Experience(
                company="Acme",
                role="Engineer",
                duration="2020 – Present",
                description=["Built dashboards"],
            )
        ],
    )
    latex = build_latex_document(profile, _sample_package())
    assert r"\documentclass" in latex
    assert "Jane Doe" in latex
    assert "Professional Summary" in latex
    assert "Built dashboards" in latex
    assert r"\end{document}" in latex


def test_generate_resume_pdf_from_package_returns_bytes():
    profile = CandidateProfile(name="Jane Doe", summary="Engineer")
    pdf_bytes, source = generate_resume_pdf_from_package(profile, _sample_package())
    assert pdf_bytes[:4] == b"%PDF"
    assert r"\documentclass" in source


def test_compile_latex_skips_when_unavailable(monkeypatch):
    monkeypatch.setattr("services.latex_service.latex_compiler_available", lambda: False)
    import pytest

    with pytest.raises(RuntimeError, match="pdflatex"):
        compile_latex_to_pdf(r"\documentclass{article}\begin{document}Hi\end{document}")
