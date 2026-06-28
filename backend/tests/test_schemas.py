import pytest
from pydantic import ValidationError

from models.schemas import (
    AppData,
    Application,
    ApplicationStatus,
    CandidateProfile,
    Skill,
    SkillChange,
)


def test_skill_confidence_bounds():
    Skill(name="React", confidence=50)
    with pytest.raises(ValidationError):
        Skill(name="React", confidence=101)
    with pytest.raises(ValidationError):
        Skill(name="React", confidence=-1)


def test_application_defaults():
    app = Application(company="Acme", role="Engineer", job_description="Build things")
    assert app.status == ApplicationStatus.submitted
    assert len(app.id) == 8
    assert app.submitted_at.endswith("Z")


def test_app_data_empty_defaults():
    data = AppData()
    assert data.applications == []
    assert data.current_profile_state is None
    assert data.reference_resume_loaded is False


def test_candidate_profile_round_trip():
    profile = CandidateProfile(
        name="Alex",
        skills=[Skill(name="Go", confidence=70)],
    )
    restored = CandidateProfile(**profile.model_dump())
    assert restored.name == "Alex"
    assert restored.skills[0].name == "Go"


def test_skill_change_fields():
    change = SkillChange(
        skill="Docker",
        previous_confidence=40,
        new_confidence=55,
        reason="Added from rejection analysis",
    )
    assert change.new_confidence > change.previous_confidence
