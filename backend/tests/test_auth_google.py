import json
from pathlib import Path

import pytest

from config import settings


@pytest.fixture()
def auth_client(tmp_path, monkeypatch):
    users_dir = tmp_path / "users"
    users_dir.mkdir()
    monkeypatch.setattr(settings, "users_dir", str(users_dir))
    monkeypatch.setattr(settings, "google_client_id", "test-client-id.apps.googleusercontent.com")

    from main import app

    with __import__("fastapi").testclient.TestClient(app) as client:
        yield client


def test_register_and_login_local(auth_client):
    res = auth_client.post(
        "/api/auth/register",
        json={"email": "user@test.com", "password": "secret12", "name": "Test User"},
    )
    assert res.status_code == 200
    assert res.json()["user"]["auth_provider"] == "local"

    res = auth_client.post(
        "/api/auth/login",
        json={"email": "user@test.com", "password": "secret12"},
    )
    assert res.status_code == 200
    assert res.json()["access_token"]


def test_google_login_creates_user(auth_client, monkeypatch):
    def fake_verify(credential: str):
        assert credential == "fake-google-token"
        return {
            "iss": "accounts.google.com",
            "sub": "google-sub-123",
            "email": "gmail.user@gmail.com",
            "email_verified": True,
            "name": "Gmail User",
            "picture": "https://example.com/photo.jpg",
        }

    monkeypatch.setattr("services.auth_service.verify_google_credential", fake_verify)

    res = auth_client.post("/api/auth/google", json={"credential": "fake-google-token"})
    assert res.status_code == 200
    body = res.json()
    assert body["user"]["email"] == "gmail.user@gmail.com"
    assert body["user"]["auth_provider"] == "google"
    assert body["user"]["picture"].startswith("https://")

    users_file = Path(settings.users_dir) / "users.json"
    data = json.loads(users_file.read_text())
    assert len(data["users"]) == 1


def test_google_login_links_existing_email_account(auth_client, monkeypatch):
    auth_client.post(
        "/api/auth/register",
        json={"email": "same@test.com", "password": "secret12", "name": "Local User"},
    )

    def fake_verify(_credential: str):
        return {
            "iss": "accounts.google.com",
            "sub": "google-sub-456",
            "email": "same@test.com",
            "email_verified": True,
            "name": "Local User",
        }

    monkeypatch.setattr("services.auth_service.verify_google_credential", fake_verify)
    res = auth_client.post("/api/auth/google", json={"credential": "token"})
    assert res.status_code == 200
    assert res.json()["user"]["auth_provider"] == "linked"


def test_local_login_rejected_for_google_only(auth_client, monkeypatch):
    def fake_verify(_credential: str):
        return {
            "iss": "accounts.google.com",
            "sub": "google-only",
            "email": "onlygoogle@gmail.com",
            "email_verified": True,
            "name": "Google Only",
        }

    monkeypatch.setattr("services.auth_service.verify_google_credential", fake_verify)
    auth_client.post("/api/auth/google", json={"credential": "token"})

    res = auth_client.post(
        "/api/auth/login",
        json={"email": "onlygoogle@gmail.com", "password": "anything"},
    )
    assert res.status_code == 401
    assert "Google" in res.json()["detail"]
