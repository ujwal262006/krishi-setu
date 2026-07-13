"""
Application configuration via environment variables.
No hardcoded secrets — everything comes from .env
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # Google Gemini
    GEMINI_API_KEY: str

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"

    # App
    APP_ENV: str = "development"
    SECRET_KEY: str = "change-me-in-production"
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]

    # Crawler defaults (overridable per-source in DB)
    DEFAULT_CRAWL_INTERVAL_HOURS: int = 24
    MAX_CRAWL_DEPTH: int = 3
    REQUEST_TIMEOUT_SECONDS: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


@lru_cache
def get_settings() -> Settings:
    """Singleton settings instance — loaded once, reused everywhere."""
    return Settings()
