from models.schemas import AppData, Application, ApplicationStatus, RejectionNote
from services.storage_service import ensure_rejection_stubs


def test_ensure_rejection_stubs_creates_missing_records():
    data = AppData(
        applications=[
            Application(
                id="app-1",
                company="Acme",
                role="Engineer",
                job_description="Python",
                missing_skills=["Docker"],
                status=ApplicationStatus.not_selected,
            )
        ],
        rejections=[],
    )
    changed = ensure_rejection_stubs(data)
    assert changed is True
    assert len(data.rejections) == 1
    assert data.rejections[0].application_id == "app-1"
    assert data.rejections[0].missing_skills == "Docker"


def test_ensure_rejection_stubs_skips_existing():
    data = AppData(
        applications=[
            Application(
                id="app-1",
                company="Acme",
                role="Engineer",
                job_description="Python",
                status=ApplicationStatus.not_selected,
            )
        ],
        rejections=[RejectionNote(application_id="app-1", notes="Already analyzed")],
    )
    changed = ensure_rejection_stubs(data)
    assert changed is False
    assert len(data.rejections) == 1
