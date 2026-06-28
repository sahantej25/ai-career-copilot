"""Guardrails: the test suite must run with zero real API keys (CI has no .env file)."""

from config import settings


def test_no_openai_key_in_test_environment():
    assert settings.openai_api_key == ""


def test_jwt_secret_is_test_only():
    assert settings.jwt_secret == "pytest-test-jwt-secret-not-for-production"
    assert "change-me" not in settings.jwt_secret.lower()


def test_google_client_id_empty_by_default():
    assert settings.google_client_id == ""
