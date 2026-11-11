"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime settings for BijliBuddy API."""

    APP_NAME: str = "BijliBuddy API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = f"sqlite:///{(BACKEND_ROOT / 'bijlibuddy.db').as_posix()}"
    JWT_SECRET_KEY: str = "dev-only-change-in-production-bijlibuddy-secret-key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 720
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    AUTO_SEED_ON_EMPTY: bool = True
    UPLOAD_DIR: str = str(BACKEND_ROOT / "uploads")
    ML_ARTIFACTS_DIR: str = str(BACKEND_ROOT / "artifacts_ml")

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        """Ensure PostgreSQL URLs use psycopg3 SQLAlchemy dialect."""
        if not value:
            return value
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+psycopg://", 1)
        if value.startswith("postgresql://") and "+psycopg" not in value:
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        return value

    @property
    def cors_origins_list(self) -> List[str]:
        """Return parsed list of allowed CORS origins."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    def validate_production_secrets(self) -> None:
        """Fail fast if production runs with the default development secret."""
        if self.ENVIRONMENT.lower() == "production" and "dev-only" in self.JWT_SECRET_KEY:
            raise RuntimeError(
                "JWT_SECRET_KEY must be explicitly set to a strong secret in production."
            )


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    settings = Settings()
    settings.validate_production_secrets()
    return settings
