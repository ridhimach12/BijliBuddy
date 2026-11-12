"""Production security tests covering demo credential protection, seeding, RBAC, and admin provisioning."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import Settings, get_settings  # noqa: E402
from app.core.constants import SERVICE_CATEGORIES_CONFIG  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.models import (  # noqa: E402
    Availability,
    Booking,
    CustomerProfile,
    ElectricianProfile,
    ElectricianSkill,
    Notification,
    Payment,
    Review,
    ServiceCategory,
    ServiceRequest,
    User,
)
from app.db.seed import ensure_service_categories, seed_database  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from scripts import create_admin as create_admin_script  # noqa: E402


def _set_env_mode(monkeypatch, *, environment: str) -> None:
    monkeypatch.setattr(
        Settings,
        "model_config",
        {**Settings.model_config, "env_file": None},
    )
    monkeypatch.setenv("ENVIRONMENT", environment)
    if environment == "production":
        monkeypatch.setenv("JWT_SECRET_KEY", "test-production-jwt-secret-key-98765")
        monkeypatch.setenv(
            "DATABASE_URL",
            "postgresql://user:pass@db.example.supabase.co:5432/postgres?sslmode=require",
        )
    else:
        monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
        monkeypatch.delenv("DATABASE_URL", raising=False)
    get_settings.cache_clear()


@pytest.fixture()
def isolated_db(tmp_path):
    db_file = tmp_path / "test_security.db"
    test_engine = create_engine(
        f"sqlite:///{db_file.as_posix()}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield test_engine, TestingSessionLocal
    finally:
        app.dependency_overrides.clear()
        test_engine.dispose()
        get_settings.cache_clear()


def test_demo_accounts_disabled_in_production(monkeypatch, isolated_db):
    _set_env_mode(monkeypatch, environment="production")
    client = TestClient(app)

    res = client.get("/api/auth/demo-accounts")
    assert res.status_code in (403, 404)
    body = res.text.lower()
    assert "admin@bijlibuddy.demo" not in body
    assert '"password"' not in body


def test_demo_accounts_works_in_development_without_admin(monkeypatch, isolated_db):
    _set_env_mode(monkeypatch, environment="development")
    client = TestClient(app)

    res = client.get("/api/auth/demo-accounts")
    assert res.status_code == 200
    payload = res.json()
    roles = {acc["role"] for acc in payload.get("accounts", [])}
    assert "customer" in roles
    assert "electrician" in roles
    assert "admin" not in roles
    assert "admin@bijlibuddy.demo" not in res.text


def test_production_seeding_creates_only_categories_and_zero_demo_data(monkeypatch, isolated_db):
    _set_env_mode(monkeypatch, environment="production")
    _, SessionMaker = isolated_db

    db = SessionMaker()
    try:
        summary = seed_database(db)
        expected_cat_names = {cfg["name"] for cfg in SERVICE_CATEGORIES_CONFIG}

        assert summary["categories"] == len(SERVICE_CATEGORIES_CONFIG)
        assert summary["categories_created"] == len(SERVICE_CATEGORIES_CONFIG)
        assert summary["customers"] == 0
        assert summary["electricians"] == 0
        assert summary["bookings"] == 0
        assert summary["admin_created"] == 0
        assert summary["production_demo_skipped"] == 1

        db_categories = db.query(ServiceCategory).all()
        assert len(db_categories) == len(SERVICE_CATEGORIES_CONFIG)
        assert {cat.name for cat in db_categories} == expected_cat_names

        # Zero demo users or user-dependent records in production
        assert db.query(User).count() == 0
        assert db.query(CustomerProfile).count() == 0
        assert db.query(ElectricianProfile).count() == 0
        assert db.query(ElectricianSkill).count() == 0
        assert db.query(Availability).count() == 0
        assert db.query(ServiceRequest).count() == 0
        assert db.query(Booking).count() == 0
        assert db.query(Review).count() == 0
        assert db.query(Payment).count() == 0
        assert db.query(Notification).count() == 0

        # Idempotent when called repeatedly
        second_summary = seed_database(db)
        assert second_summary["categories"] == len(SERVICE_CATEGORIES_CONFIG)
        assert second_summary["categories_created"] == 0
        assert db.query(ServiceCategory).count() == len(SERVICE_CATEGORIES_CONFIG)
        assert db.query(User).count() == 0
    finally:
        db.close()


def test_production_categories_and_real_admin_startup_without_demo_users(monkeypatch, isolated_db):
    _set_env_mode(monkeypatch, environment="production")
    _, SessionMaker = isolated_db
    client = TestClient(app)

    admin_secret = "RealProductionAdminPass#2026"
    db = SessionMaker()
    try:
        # Real admin provisioned BEFORE seed_database / ensure_service_categories runs
        admin_user = create_admin_script.create_admin_user(
            db,
            email="lead.admin@bijlibuddy.org",
            full_name="Lead Platform Admin",
            phone="+919810011223",
            password=admin_secret,
        )
        assert admin_user.role == "admin"
        assert admin_user.is_demo is False

        # Even with an existing User row, required categories must initialize without demo users
        cats_map, created = ensure_service_categories(db)
        db.commit()
        assert len(cats_map) == len(SERVICE_CATEGORIES_CONFIG)
        assert created == len(SERVICE_CATEGORIES_CONFIG)

        summary = seed_database(db)
        assert summary["categories"] == len(SERVICE_CATEGORIES_CONFIG)
        assert summary["customers"] == 0
        assert summary["electricians"] == 0
        assert summary["bookings"] == 0
        assert summary["admin_created"] == 0

        assert db.query(User).count() == 1
        assert db.query(User).filter(User.is_demo.is_(True)).count() == 0
        assert db.query(Booking).count() == 0
    finally:
        db.close()

    cat_res = client.get("/api/public/categories")
    assert cat_res.status_code == 200
    assert len(cat_res.json()["categories"]) == len(SERVICE_CATEGORIES_CONFIG)

    login_res = client.post(
        "/api/auth/login",
        json={"email": "lead.admin@bijlibuddy.org", "password": admin_secret},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    for admin_endpoint in (
        "/api/admin/overview",
        "/api/admin/demand-analytics",
        "/api/admin/leaderboard",
    ):
        ep_res = client.get(admin_endpoint, headers=headers)
        assert ep_res.status_code == 200, ep_res.text


def test_development_seeding_continues_unchanged(monkeypatch, isolated_db):
    _set_env_mode(monkeypatch, environment="development")
    _, SessionMaker = isolated_db

    db = SessionMaker()
    try:
        summary = seed_database(db)
        assert summary["categories"] == len(SERVICE_CATEGORIES_CONFIG)
        assert summary["admin_created"] == 1
        assert summary["customers"] == 8
        assert summary["electricians"] == 22
        assert summary["bookings"] == 68
        assert db.query(User).filter(User.is_demo.is_(True)).count() == 31
        assert db.query(Booking).count() == 68
        assert db.query(Notification).count() == 3
    finally:
        db.close()


def test_public_registration_cannot_create_admin(monkeypatch, isolated_db):
    _set_env_mode(monkeypatch, environment="production")
    _, SessionMaker = isolated_db
    client = TestClient(app)

    res = client.post(
        "/api/auth/register",
        json={
            "full_name": "Unauthorized Admin",
            "email": "attacker-admin@example.com",
            "phone": "+919811112222",
            "password": "StrongPassword123",
            "role": "admin",
        },
    )
    assert res.status_code == 422

    # Normal customer registration still works in production
    cust_res = client.post(
        "/api/auth/register",
        json={
            "full_name": "Valid Customer",
            "email": "valid.customer@example.com",
            "phone": "+919811113333",
            "password": "StrongPassword123",
            "role": "customer",
            "locality": "Saket",
        },
    )
    assert cust_res.status_code == 201
    assert cust_res.json()["user"]["role"] == "customer"

    db = SessionMaker()
    try:
        assert db.query(User).filter(User.role == "admin").count() == 0
    finally:
        db.close()


def test_no_production_public_endpoint_exposes_admin_or_passwords(monkeypatch, isolated_db):
    _set_env_mode(monkeypatch, environment="production")
    _, SessionMaker = isolated_db

    db = SessionMaker()
    try:
        seed_database(db)
    finally:
        db.close()

    client = TestClient(app)
    endpoints = [
        "/api/health",
        "/api/auth/demo-accounts",
        "/api/public/categories",
        "/api/public/localities",
        "/api/public/electricians",
    ]
    for path in endpoints:
        res = client.get(path)
        body = res.text.lower()
        assert "admin@bijlibuddy.demo" not in body
        assert "password_hash" not in body
        assert '"password"' not in body


def test_create_admin_script_provisions_admin_without_logging_secret(
    monkeypatch, isolated_db, capsys
):
    _set_env_mode(monkeypatch, environment="production")
    test_engine, SessionMaker = isolated_db
    client = TestClient(app)

    monkeypatch.setattr(create_admin_script, "engine", test_engine)
    monkeypatch.setattr(create_admin_script, "SessionLocal", SessionMaker)

    secret_pw = "PrivatelySuppliedAdmin#2026"
    monkeypatch.setenv("ADMIN_PASSWORD", secret_pw)

    exit_code = create_admin_script.main(
        [
            "--email",
            "ops.admin@bijlibuddy.org",
            "--name",
            "Platform Operations",
            "--phone",
            "9810099887",
        ]
    )
    assert exit_code == 0

    captured = capsys.readouterr()
    combined_output = captured.out + captured.err
    assert secret_pw not in combined_output
    assert "password_hash" not in combined_output
    assert "ops.admin@bijlibuddy.org" in captured.out

    # Provisioned admin can authenticate with supplied password, never with wrong password
    ok_login = client.post(
        "/api/auth/login",
        json={"email": "ops.admin@bijlibuddy.org", "password": secret_pw},
    )
    assert ok_login.status_code == 200
    assert ok_login.json()["user"]["role"] == "admin"
    assert ok_login.json()["user"]["is_demo"] is False

    bad_login = client.post(
        "/api/auth/login",
        json={"email": "ops.admin@bijlibuddy.org", "password": "WrongPassword123"},
    )
    assert bad_login.status_code == 401

    # Duplicate email and weak password are rejected
    db = SessionMaker()
    try:
        with pytest.raises(ValueError, match="at least"):
            create_admin_script.create_admin_user(
                db,
                email="second.admin@bijlibuddy.org",
                full_name="Second Admin",
                phone="9810099888",
                password="short",
            )
        with pytest.raises(ValueError, match="already exists"):
            create_admin_script.create_admin_user(
                db,
                email="ops.admin@bijlibuddy.org",
                full_name="Duplicate Admin",
                phone="9810099889",
                password=secret_pw,
            )
    finally:
        db.close()
