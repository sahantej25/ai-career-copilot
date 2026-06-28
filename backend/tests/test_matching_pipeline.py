"""Tests for step-by-step matching and resume pipeline helpers."""
from models.schemas import CandidateProfile, Experience, MatchContextInput, Project, Skill
from agents.shared.profile_context import build_profile_context
from agents.matching_pipeline import _parse_score_breakdown, _parse_steps
from agents.resume_pipeline import (
    _ensure_bullet_count,
    _fallback_experience,
    _match_context_block,
    _merge_tailored_with_profile,
    _parse_tailored_experience,
)
from agents.resume_structure_agents import infer_section_order_heuristic
from models.schemas import TailoredExperienceEntry


def _sample_profile() -> CandidateProfile:
    return CandidateProfile(
        name="Jane Doe",
        summary="Full-stack engineer",
        skills=[Skill(name="React", confidence=90, category="frontend")],
        experience=[
            Experience(
                company="Acme",
                role="Senior Engineer",
                duration="2020 – Present",
                description=["Built React dashboards serving 50k users"],
            )
        ],
        projects=[Project(name="Career Copilot", description="AI job assistant", technologies=["React"])],
    )


def test_build_profile_context_includes_experience_bullets():
    ctx = build_profile_context(_sample_profile())
    assert "Built React dashboards" in ctx
    assert "Senior Engineer at Acme" in ctx


def test_parse_score_breakdown_clamps():
    result = _parse_score_breakdown({"skills": 120, "experience": 70, "projects": 65, "domain": 75})
    assert result["skills"] == 100.0
    assert result["experience"] == 70.0


def test_parse_steps_from_llm_shape():
    steps = _parse_steps([
        {"step": 1, "title": "Extract JD", "summary": "Parsed senior role requirements"},
        {"step": 2, "title": "Map evidence", "summary": "Found React alignment"},
    ])
    assert len(steps) == 2
    assert steps[0].title == "Extract JD"


def test_match_context_block_includes_highlights():
    block = _match_context_block(
        MatchContextInput(
            match_percentage=82,
            matched_skills=["React"],
            missing_skills=["GraphQL"],
            experience_highlights=["Led React migration at Acme"],
        )
    )
    assert "82" in block
    assert "React migration" in block


def test_parse_tailored_experience_fallback():
    profile = _sample_profile()
    entries = _parse_tailored_experience([], profile)
    assert len(entries) == 1
    assert entries[0].company == "Acme"


def test_parse_tailored_experience_from_llm():
    profile = _sample_profile()
    entries = _parse_tailored_experience(
        [{"company": "Acme", "role": "Senior Engineer", "duration": "2020 – Present", "bullets": ["Delivered X"]}],
        profile,
    )
    assert entries[0].bullets == ["Delivered X"]


def test_ensure_bullet_count_pads_missing_rewrites():
    original = [
        "Built React dashboards serving 50k users",
        "Led migration to TypeScript across 12 services",
        "Mentored 4 junior engineers",
    ]
    result = _ensure_bullet_count(["Built React dashboards serving 50k users"], original)
    assert len(result) == 3
    assert result[0] == "Built React dashboards serving 50k users"
    assert "TypeScript" in result[1]


def test_merge_tailored_with_profile_keeps_missing_roles():
    profile = CandidateProfile(
        name="Jane Doe",
        experience=[
            Experience(
                company="Acme",
                role="Senior Engineer",
                duration="2020 – Present",
                description=["Bullet A", "Bullet B"],
            ),
            Experience(
                company="Beta Corp",
                role="Engineer",
                duration="2018 – 2020",
                description=["Legacy work"],
            ),
        ],
    )
    tailored = [
        TailoredExperienceEntry(
            company="Acme",
            role="Senior Engineer",
            duration="2020 – Present",
            bullets=["Tailored A"],
        )
    ]
    merged = _merge_tailored_with_profile(tailored, profile)
    assert len(merged) == 2
    assert len(merged[0].bullets) == 2
    assert merged[1].company == "Beta Corp"


def test_infer_section_order_empty_text():
    order = infer_section_order_heuristic("")
    assert "summary" in order
    assert "experience" in order
