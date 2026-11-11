"""Unit tests for production configuration & database URL validation."""

import pytest

from app.core.config import Settings, get_settings


def test_production_with_postgresql_url_passes_and_normalizes():
    s1 = Settings(
        _env_file=None,
        ENVIRONMENT="production",
        JWT_SECRET_KEY="super-strong-prod-secret-value",
        DATABASE_URL="postgresql://user:pass@db.example.supabase.co:5432/postgres?sslmode=require",
    )
    s1.validate_production_secrets()
    assert s1.DATABASE_URL.startswith("postgresql+psycopg://")

    s2 = Settings(
        _env_file=None,
        ENVIRONMENT="production",
        JWT_SECRET_KEY="super-strong-prod-secret-value",
        DATABASE_URL="postgres://user:pass@db.example.supabase.co:5432/postgres",
    )
    s2.validate_production_secrets()
    assert s2.DATABASE_URL.startswith("postgresql+psycopg://")


def test_production_with_sqlite_url_raises_runtime_error():
    settings = Settings(
        _env_file=None,
        ENVIRONMENT="production",
        JWT_SECRET_KEY="super-strong-prod-secret-value",
        DATABASE_URL="sqlite:///./bijlibuddy.db",
    )
    with pytest.raises(RuntimeError, match="PostgreSQL"):
        settings.validate_production_secrets()


def test_production_with_empty_or_missing_database_url_raises_runtime_error(monkeypatch):
    # Explicit empty / whitespace DATABASE_URL
    for blank in ("", "   "):
        empty_settings = Settings(
            _env_file=None,
            ENVIRONMENT="production",
            JWT_SECRET_KEY="super-strong-prod-secret-value",
            DATABASE_URL=blank,
        )
        with pytest.raises(RuntimeError, match="PostgreSQL"):
            empty_settings.validate_production_secrets()

    # Completely omitted DATABASE_URL (falls back to SQLite default)
    omitted_settings = Settings(
        _env_file=None,
        ENVIRONMENT="production",
        JWT_SECRET_KEY="super-strong-prod-secret-value",
    )
    with pytest.raises(RuntimeError, match="PostgreSQL"):
        omitted_settings.validate_production_secrets()

    # Missing DATABASE_URL via get_settings()
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("JWT_SECRET_KEY", "super-strong-prod-secret-value")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(
        Settings,
        "model_config",
        {**Settings.model_config, "env_file": None},
    )
    get_settings.cache_clear()
    try:
        with pytest.raises(RuntimeError, match="PostgreSQL"):
            get_settings()
    finally:
        get_settings.cache_clear()


def test_development_with_sqlite_remains_supported():
    settings = Settings(
        _env_file=None,
        ENVIRONMENT="development",
        DATABASE_URL="sqlite:///./local_dev.db",
    )
    settings.validate_production_secrets()
    assert settings.DATABASE_URL == "sqlite:///./local_dev.db"
