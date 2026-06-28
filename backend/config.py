from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).parent


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    data_file_path: str = str(BASE_DIR / "data" / "data.json")
    max_file_size_mb: int = 10
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5199"]
    jwt_secret: str = "change-me-in-production-use-env-var"
    jwt_expire_hours: int = 168
    users_dir: str = str(BASE_DIR / "data" / "users")
    linkedin_default_location: str = "United States"
    greenhouse_boards: list[str] = [
        "stripe", "figma", "discord", "notion", "airbnb", "datadog",
        "cloudflare", "openai", "databricks", "scaleai", "brex", "ramp",
    ]
    google_client_id: str = ""
    # AI guardrails
    ai_rate_limit_requests: int = 30
    ai_rate_limit_window_seconds: int = 3600
    openai_max_tokens: int = 4096
    openai_timeout_seconds: float = 60.0
    max_request_body_mb: int = 12

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
