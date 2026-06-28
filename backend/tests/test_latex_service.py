"""Tests for LaTeX resume builder and PyLaTeX compiler."""
from models.schemas import CandidateProfile, Experience, ResumePreviewResponse, Skill, TailoredExperienceEntry
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
    dirty = r"\documentclass{article}\write18{evil}"
    cleaned = sanitize_latex_source(dirty)
    assert r"\write18" not in cleaned


def test_build_latex_document_uses_reference_template():
    profile = CandidateProfile(
        name="Jane Doe",
        email="jane@example.com",
        location="Austin, TX",
        skills=[
            Skill(name="React", confidence=90, category="frontend"),
            Skill(name="Python", confidence=85, category="programming"),
        ],
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
    assert r"\documentclass[letterpaper,10pt" in latex
    assert r"\scshape JANE DOE" in latex
    assert r"\color{Blue} Professional Summary" in latex
    assert r"\color{Blue} Technical Skills" in latex
    assert r"\color{Blue} Experience" in latex
    assert "Built dashboards" in latex
    assert r"\end{document}" in latex


def test_build_latex_includes_publications_from_original():
    from models.schemas import ResumeSnapshot

    profile = CandidateProfile(name="Jane Doe", summary="Engineer")
    original = ResumeSnapshot(
        raw_text=(
            "PUBLICATIONS\n"
            "1. Paper A at ACM 2024.\n"
            "TECHNICAL SKILLS\nPython"
        ),
    )
    latex = build_latex_document(profile, _sample_package(), original=original)
    assert r"\color{Blue} Publications" in latex
    assert "ACM 2024" in latex


def test_generate_resume_pdf_from_package_returns_bytes():
    profile = CandidateProfile(name="Jane Doe", summary="Engineer")
    pdf_bytes, source = generate_resume_pdf_from_package(profile, _sample_package())
    assert pdf_bytes[:4] == b"%PDF"
    assert r"\documentclass" in source


def test_compile_latex_raises_when_pylatex_unavailable(monkeypatch):
    monkeypatch.setattr("services.latex_service.pylatex_compiler_available", lambda: False)
    import pytest

    with pytest.raises(RuntimeError, match="PyLaTeX"):
        compile_latex_to_pdf(r"\documentclass{article}\begin{document}Hi\end{document}")
