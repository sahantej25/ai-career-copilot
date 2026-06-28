import json

import pytest

from models.schemas import Application, ApplicationStatus, ProfileUpdate, RejectionNote, SkillChange
from services import storage_service as store


@pytest.mark.asyncio
async def test_load_and_save_data(temp_data_file):
    data = await store.load_data()
    assert data.applications == []

    data.reference_resume_loaded = True
    data.reference_resume_name = "reference.pdf"
    await store.save_data(data)

    reloaded = await store.load_data()
    assert reloaded.reference_resume_loaded is True
    assert reloaded.reference_resume_name == "reference.pdf"
    assert temp_data_file.exists()


@pytest.mark.asyncio
async def test_reset_data_clears_state(seed_data):
    data = await store.load_data()
    assert len(data.applications) == 1

    fresh = await store.reset_data()
    assert fresh.applications == []
    assert fresh.current_profile_state is None

    reloaded = await store.load_data()
    assert reloaded.applications == []


@pytest.mark.asyncio
async def test_upsert_application_insert_and_update(seed_data):
    new_app = Application(
        id="app-new99",
        company="Globex",
        role="Backend Engineer",
        job_description="Python, FastAPI",
    )
    await store.upsert_application(new_app)

    data = await store.load_data()
    assert len(data.applications) == 2
    assert data.applications[0].id == "app-new99"

    new_app.status = ApplicationStatus.interview
    await store.upsert_application(new_app)

    updated = await store.get_application("app-new99")
    assert updated is not None
    assert updated.status == ApplicationStatus.interview


@pytest.mark.asyncio
async def test_upsert_rejection(seed_data):
    rejection = RejectionNote(
        application_id="app-test01",
        notes="Struggled with system design questions.",
        summary="Focus on distributed systems.",
    )
    await store.upsert_rejection(rejection)

    data = await store.load_data()
    assert len(data.rejections) == 1
    assert data.rejections[0].summary == "Focus on distributed systems."


@pytest.mark.asyncio
async def test_add_profile_update(seed_data):
    update = ProfileUpdate(
        triggered_by="app-test01",
        company="Acme Inc",
        changes=[
            SkillChange(
                skill="GraphQL",
                previous_confidence=0,
                new_confidence=45,
                reason="Identified gap from rejection",
            )
        ],
        recommendations=["Study GraphQL fundamentals"],
    )
    await store.add_profile_update(update)

    data = await store.load_data()
    assert len(data.profile_update_history) == 1
    assert data.profile_update_history[0].changes[0].skill == "GraphQL"
