def test_list_applications_empty(client):
    response = client.get("/api/tracking/applications")
    assert response.status_code == 200
    assert response.json() == []


def test_list_applications_with_seed(client, seed_data):
    response = client.get("/api/tracking/applications")
    assert response.status_code == 200
    apps = response.json()
    assert len(apps) == 1
    assert apps[0]["company"] == "Acme Inc"


def test_get_application_by_id(client, seed_data):
    response = client.get("/api/tracking/applications/app-test01")
    assert response.status_code == 200
    assert response.json()["role"] == "Frontend Engineer"


def test_get_application_not_found(client):
    response = client.get("/api/tracking/applications/missing-id")
    assert response.status_code == 404


def test_update_application_status(client, seed_data):
    response = client.put(
        "/api/tracking/applications/app-test01/status",
        json={"status": "interview"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "interview"

    listed = client.get("/api/tracking/applications").json()
    assert listed[0]["status"] == "interview"


def test_delete_application(client, seed_data):
    response = client.delete("/api/tracking/applications/app-test01")
    assert response.status_code == 200

    listed = client.get("/api/tracking/applications").json()
    assert listed == []
