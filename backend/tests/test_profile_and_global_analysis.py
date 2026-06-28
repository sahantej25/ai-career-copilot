"""Tests for manual profile save and global analysis rejection sync."""


def test_save_profile_manual(client, sample_profile):
    response = client.put("/api/apply/profile", json=sample_profile)
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Jane Doe"
    assert len(body["skills"]) == 2

    get_resp = client.get("/api/apply/profile")
    assert get_resp.status_code == 200
    assert get_resp.json()["email"] == "jane@example.com"


def test_save_profile_requires_content(client):
    response = client.put("/api/apply/profile", json={
        "name": "",
        "email": "",
        "summary": "",
        "skills": [],
        "projects": [],
        "experience": [],
        "education": [],
        "domains": [],
    })
    assert response.status_code == 422


def test_clear_profile(client, sample_profile):
    client.put("/api/apply/profile", json=sample_profile)
    response = client.delete("/api/apply/profile")
    assert response.status_code == 200

    get_resp = client.get("/api/apply/profile")
    assert get_resp.status_code == 404


def test_global_refresh_requires_rejected_apps(client, sample_profile):
    client.put("/api/apply/profile", json=sample_profile)
    response = client.post("/api/analysis/global/refresh")
    assert response.status_code == 400
    assert "Not Selected" in response.json()["detail"]


def test_global_refresh_requires_profile(client, seed_data):
    client.delete("/api/apply/profile")
    client.put(
        "/api/tracking/applications/app-test01/status",
        json={"status": "not_selected"},
    )
    response = client.post("/api/analysis/global/refresh")
    assert response.status_code == 400
    assert "profile" in response.json()["detail"].lower()


def test_not_selected_status_creates_rejection_stub(client, seed_data):
    response = client.put(
        "/api/tracking/applications/app-test01/status",
        json={"status": "not_selected"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "not_selected"

    data = client.get("/api/data").json()
    assert len(data["rejections"]) == 1
    assert data["rejections"][0]["application_id"] == "app-test01"
    assert "GraphQL" in data["rejections"][0]["missing_skills"]
