def test_get_all_data_empty(client):
    response = client.get("/api/data")
    assert response.status_code == 200
    body = response.json()
    assert body["applications"] == []
    assert body["current_profile_state"] is None


def test_get_all_data_with_seed(client, seed_data):
    response = client.get("/api/data")
    assert response.status_code == 200
    body = response.json()
    assert len(body["applications"]) == 1
    assert body["current_profile_state"]["name"] == "Jane Doe"


def test_clear_all_data(client, seed_data):
    assert client.get("/api/data").json()["applications"]

    response = client.post("/api/data/clear")
    assert response.status_code == 200
    body = response.json()
    assert "cleared" in body["message"].lower()
    assert body["data"]["applications"] == []

    after = client.get("/api/data").json()
    assert after["applications"] == []
    assert after["current_profile_state"] is None
