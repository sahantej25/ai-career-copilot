from unittest.mock import AsyncMock, patch

from models.schemas import JobListing


@patch("routers.jobs.fetch_job_feed", new_callable=AsyncMock)
@patch("routers.jobs.store.load_data", new_callable=AsyncMock)
def test_job_feed_endpoint(mock_load, mock_fetch, client):
    mock_fetch.return_value = (
        [
            JobListing(
                id="remotive:99",
                title="Frontend Developer",
                company="TestCo",
                description="React role",
                apply_url="https://example.com/job",
                source="remotive",
            )
        ],
        ["remotive"],
    )
    mock_load.return_value.current_profile_state = None

    response = client.get("/api/jobs?limit=5&match=false")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["jobs"][0]["company"] == "TestCo"


def test_job_sources_endpoint(client):
    response = client.get("/api/jobs/sources")
    assert response.status_code == 200
    assert "linkedin" in response.json()["sources"]
