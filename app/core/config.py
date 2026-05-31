"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Google AI
    google_api_key: str = "your_google_api_key_here"
    gemini_model: str = "gemini-2.0-flash"  # Use gemini-pro as fallback if unavailable

    # Redis & Celery
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # File uploads
    max_file_size_mb: int = 10
    upload_dir: str = "/tmp/docai_uploads"
    allowed_extensions: list[str] = [".pdf", ".txt", ".docx", ".md"]

    # Cache TTL in seconds
    cache_ttl_seconds: int = 3600

    # App
    app_env: str = "development"
    app_title: str = "DocAI — Intelligent Document Q&A"
    app_version: str = "1.0.0"


settings = Settings()
