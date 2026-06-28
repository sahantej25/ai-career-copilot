import json
import os
from pathlib import Path

# Tests must never use real secrets from backend/.env (gitignored, not in GitHub).
# Force safe values before Settings() loads — env vars override .env in pydantic-settings.
os.environ["OPENAI_API_KEY"] = ""
os.environ["JWT_SECRET"] = "pytest-test-jwt-secret-not-for-production"
os.environ["GOOGLE_CLIENT_ID"] = ""

import pytest
from fastapi.testclient import TestClient

from config import settings


@pytest.fixture(autouse=True)
def isolate_test_secrets(monkeypatch):
    """Ensure no test reads OpenAI/Google/JWT secrets from a developer's local .env."""
    monkeypatch.setattr(settings, "openai_api_key", "")
    monkeypatch.setattr(settings, "google_client_id", "")
    monkeypatch.setattr(settings, "jwt_secret", "pytest-test-jwt-secret-not-for-production")

    import services.openai_service as openai_service

    monkeypatch.setattr(openai_service, "_client", None)


@pytest.fixture()
def temp_data_file(tmp_path, monkeypatch):
    """Point storage at an isolated JSON file for each test."""
    data_path = tmp_path / "data.json"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(settings, "data_file_path", str(data_path))
    yield data_path


@pytest.fixture()
def client(temp_data_file, monkeypatch):
    """FastAPI test client with fresh data file and auth bypass."""
    from main import app
    from deps.auth import bind_user_context
    from models.schemas import UserPublic

    async def _fake_auth():
        return UserPublic(id="test-user", email="test@test.com", name="Test User")

    app.dependency_overrides[bind_user_context] = _fake_auth
    monkeypatch.setattr(
        "services.storage_service._resolve_path",
        lambda: Path(settings.data_file_path),
    )

    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def sample_profile():
    return {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "555-0100",
        "location": "San Francisco, CA",
        "summary": "Full-stack engineer with 8 years of experience.",
        "skills": [
            {"name": "React", "confidence": 90, "category": "frontend"},
            {"name": "Python", "confidence": 85, "category": "backend"},
        ],
        "projects": [
            {
                "name": "Career Copilot",
                "description": "AI job application assistant",
                "technologies": ["React", "FastAPI"],
            }
        ],
        "experience": [
            {
                "company": "Tech Corp",
                "role": "Senior Engineer",
                "duration": "2020 – Present",
                "description": ["Led frontend platform migration"],
            }
        ],
        "education": [
            {"degree": "B.S. Computer Science", "institution": "State University", "year": "2016"}
        ],
        "domains": ["web", "ai"],
    }


@pytest.fixture()
def seed_data(temp_data_file, sample_profile):
    """Pre-populate the temp data file with one application."""
    payload = {
        "metadata": {"version": "1.0.0", "created_at": "2026-01-01T00:00:00Z", "last_updated": "2026-01-01T00:00:00Z"},
        "current_profile_state": sample_profile,
        "applications": [
            {
                "id": "app-test01",
                "company": "Acme Inc",
                "role": "Frontend Engineer",
                "job_description": "React, TypeScript, Tailwind",
                "match_percentage": 82.0,
                "matched_skills": ["React", "TypeScript"],
                "missing_skills": ["GraphQL"],
                "status": "submitted",
                "submitted_at": "2026-01-15T10:00:00Z",
                "updated_at": "2026-01-15T10:00:00Z",
                "resume_filename": "resume_acme.pdf",
            }
        ],
        "rejections": [],
        "profile_update_history": [],
        "global_analysis": None,
        "resume_style": None,
        "reference_resume_loaded": False,
        "reference_resume_name": "",
    }
    temp_data_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
