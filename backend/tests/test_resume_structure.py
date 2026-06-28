"""Tests for resume structure heuristics and section order resolution."""
from agents.resume_structure_agents import infer_section_order_heuristic, resolve_section_order
from models.schemas import ResumeSnapshot, ResumeStyle


def test_infer_section_order_from_headings():
    raw = """
    John Doe
    PROFESSIONAL SUMMARY
    Experienced engineer...
    SKILLS
    React, Python
    EXPERIENCE
    Acme Corp
    EDUCATION
    B.S. CS
    """
    order = infer_section_order_heuristic(raw)
    assert order.index("summary") < order.index("skills")
    assert order.index("skills") < order.index("experience")
    assert order.index("experience") < order.index("education")


def test_resolve_section_order_prefers_structure():
    style = ResumeStyle(section_order=["skills", "summary", "experience", "projects", "education"])
    snapshot = ResumeSnapshot(section_order=["experience", "summary", "skills", "projects", "education"])
    order = resolve_section_order(
        ["summary", "experience", "skills", "projects", "education"],
        style,
        snapshot,
    )
    assert order[0] == "summary"
    assert order[1] == "experience"
