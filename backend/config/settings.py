from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: PostgresDsn
    ENVIRONMENT: str = "development"
    APP_VERSION: str = "0.1.0"
    APP_TITLE: str = "Library Management Service"

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    # Production-safe defaults — only the methods and headers the frontend requires.
    # Override to ["*"] via environment variables for local development if needed.
    CORS_HEADERS: list[str] = ["Authorization", "Content-Type"]
    CORS_METHODS: list[str] = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]

    SECRET_KEY: Annotated[str, Field(min_length=32)]
    ALGORITHM: Literal["HS256", "RS256"] = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 10_080  # 7 days
    LOG_LEVEL: str = "INFO"

    # Token revocation store.
    # Set to a Redis URL (e.g. redis://localhost:6379/0) to share the blocklist
    # across all workers and replicas. When unset, an in-process fallback is used
    # (single-worker / development only).
    REDIS_URL: str | None = None

    OVERDUE_SCAN_INTERVAL_SECONDS: int = 300


settings = Settings()
