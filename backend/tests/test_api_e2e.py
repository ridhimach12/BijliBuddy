"""End-to-end API integration test covering all 13 required marketplace workflows + RBAC + safety."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.seed import seed_database
from app.db.session import get_db
from app.main import app


@pytest.fixture()
def client(tmp_path):
    db_file = tmp_path / "test_e2e.db"
    test_engine = create_engine(
        f"sqlite:///{db_file.as_posix()}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    seed_db = TestingSessionLocal()
    try:
        seed_database(seed_db)
    finally:
        seed_db.close()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _login(client: TestClient, email: str, password: str = "Demo@1234") -> str:
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def test_registration_indian_phone_validation_and_unverified_default(client: TestClient):
    # Invalid Indian phone rejected
    bad = client.post(
        "/api/auth/register",
        json={
            "full_name": "Invalid Phone",
            "email": "badphone@example.com",
            "phone": "12345",
            "password": "Password123",
            "role": "customer",
        },
    )
    assert bad.status_code == 422

    # New electrician registers with credential_id -> MUST remain 'pending', NEVER 'verified'
    elec_reg = client.post(
        "/api/auth/register",
        json={
            "full_name": "Sandeep Kumar",
            "email": "sandeep.new@example.com",
            "phone": "9811223344",
            "password": "Password123",
            "role": "electrician",
            "locality": "Saket",
            "experience_years": 3,
            "service_radius_km": 7.0,
            "skills": ["MCB/circuit breaker", "Wiring"],
            "credential_id": "DL-WIRE-2026-999",
        },
    )
    assert elec_reg.status_code == 201, elec_reg.text
    data = elec_reg.json()
    assert data["user"]["phone"] == "+919811223344"
    assert data["user"]["verification_status"] == "pending"


def test_full_end_to_end_booking_and_admin_workflow(client: TestClient):
    # 1. Customer logs in (seeded demo customer)
    cust_token = _login(client, "ananya.sharma@bijlibuddy.demo")
    cust_headers = {"Authorization": f"Bearer {cust_token}"}

    # Verify RBAC blocks customer from admin & electrician endpoints
    assert client.get("/api/admin/overview", headers=cust_headers).status_code == 403
    assert client.get("/api/electricians/dashboard", headers=cust_headers).status_code == 403

    # 2-5. Customer submits service request -> AI classification + hazard warning + RF price + Top 5 match
    sr_res = client.post(
        "/api/customers/service-requests",
        headers=cust_headers,
        json={
            "description": "Main MCB tripping with sparks and burning smell in bedroom",
            "urgency": "emergency",
            "time_of_service": "evening",
            "address": "B-42, Press Enclave Road, Saket",
            "locality": "Saket",
        },
    )
    assert sr_res.status_code == 201, sr_res.text
    sr_payload = sr_res.json()

    assert sr_payload["classification"]["predicted_category"] == "MCB/circuit breaker"
    assert sr_payload["classification"]["hazard_assessment"]["hazard_detected"] is True
    assert sr_payload["classification"]["hazard_assessment"]["severity"] == "critical"

    price = sr_payload["price_estimate"]
    assert price["lower_estimate_inr"] <= price["predicted_base_price_inr"] <= price["upper_estimate_inr"]

    recs = sr_payload["matching"]["recommendations"]
    assert 1 <= len(recs) <= 5
    # Top recommended electrician in Saket for MCB must be available
    assert recs[0]["is_available"] is True

    # Pick Ramesh Kumar Verma (seeded Saket verified MCB electrician) or top match
    selected_elec_id = recs[0]["electrician_id"]
    # Find Ramesh specifically if in recommendations so we can log into Ramesh's account
    ramesh_match = next((r for r in recs if "Ramesh" in r["full_name"]), None)
    if ramesh_match:
        selected_elec_id = ramesh_match["electrician_id"]

    # 7. Customer creates booking
    book_res = client.post(
        "/api/customers/bookings",
        headers=cust_headers,
        json={
            "service_request_id": sr_payload["service_request"]["id"],
            "electrician_id": selected_elec_id,
            "scheduled_slot": "Immediate Dispatch",
            "time_slot_bucket": "Evening (5PM-9PM)",
            "customer_notes": "Near Gate 2",
        },
    )
    assert book_res.status_code == 201, book_res.text
    booking_id = book_res.json()["booking"]["id"]
    assert book_res.json()["booking"]["status"] == "pending"

    # 8. Electrician logs in & sees incoming request
    # Determine email of selected electrician
    elec_email = "ramesh.verma@bijlibuddy.demo" if ramesh_match else None
    if elec_email is None:
        admin_tok = _login(client, "admin@bijlibuddy.demo")
        all_elecs = client.get(
            "/api/admin/electricians", headers={"Authorization": f"Bearer {admin_tok}"}
        ).json()["electricians"]
        elec_email = next(e["email"] for e in all_elecs if e["id"] == selected_elec_id)

    elec_token = _login(client, elec_email)
    elec_headers = {"Authorization": f"Bearer {elec_token}"}

    dash_before = client.get("/api/electricians/dashboard", headers=elec_headers)
    assert dash_before.status_code == 200
    incoming_ids = [b["id"] for b in dash_before.json()["incoming_requests"]]
    assert booking_id in incoming_ids

    # 9. Electrician accepts booking with explicit quotation
    acc_res = client.post(
        f"/api/electricians/bookings/{booking_id}/respond",
        headers=elec_headers,
        json={
            "action": "accept",
            "electrician_quote_inr": 650,
            "electrician_notes": "On my way with 32A MCB unit check tools.",
        },
    )
    assert acc_res.status_code == 200
    assert acc_res.json()["booking"]["status"] == "accepted"
    assert acc_res.json()["booking"]["electrician_quote_inr"] == 650

    # 10. Customer polls booking status -> sees accepted
    cust_poll = client.get(f"/api/bookings/{booking_id}", headers=cust_headers)
    assert cust_poll.status_code == 200
    assert cust_poll.json()["booking"]["status"] == "accepted"

    # 11. Electrician starts & completes job
    assert client.post(f"/api/electricians/bookings/{booking_id}/start", headers=elec_headers).status_code == 200
    comp_res = client.post(
        f"/api/electricians/bookings/{booking_id}/complete",
        headers=elec_headers,
        json={"final_amount_inr": 680, "on_time_completed": True, "electrician_notes": "Replaced faulty breaker"},
    )
    assert comp_res.status_code == 200
    assert comp_res.json()["booking"]["status"] == "completed"
    assert comp_res.json()["booking"]["final_amount_inr"] == 680

    # 12. Customer confirms sandbox payment & submits review
    pay_res = client.post(
        f"/api/bookings/{booking_id}/sandbox-payment",
        headers=cust_headers,
        json={"payment_method": "sandbox_upi"},
    )
    assert pay_res.status_code == 200
    assert pay_res.json()["booking"]["payment"]["is_sandbox"] is True
    assert pay_res.json()["booking"]["payment"]["status"] == "demo_paid"

    rev_res = client.post(
        f"/api/customers/bookings/{booking_id}/review",
        headers=cust_headers,
        json={"rating": 5, "comment": "Super fast emergency response!", "was_on_time": True},
    )
    assert rev_res.status_code == 201
    assert rev_res.json()["review"]["rating"] == 5

    # 13. Admin checks overview, demand analytics, and verifies a pending electrician
    admin_token = _login(client, "admin@bijlibuddy.demo")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    overview = client.get("/api/admin/overview", headers=admin_headers).json()
    assert overview["kpis"]["total_bookings"] == 69  # 68 seeded + 1 new E2E booking
    assert overview["kpis"]["completed_bookings"] == 53  # 52 seeded + 1 completed

    demand = client.get("/api/admin/demand-analytics", headers=admin_headers).json()
    assert demand["total_analyzed_bookings"] == 69
    assert len(demand["forecast_next_days"]) == 7

    elecs_admin = client.get("/api/admin/electricians", headers=admin_headers).json()["electricians"]
    pending_elec = next(e for e in elecs_admin if e["verification_status"] == "pending" and e["credential_id"])
    ver_res = client.post(
        f"/api/admin/electricians/{pending_elec['id']}/verify",
        headers=admin_headers,
        json={"decision": "verified", "verification_notes": "License validated by admin"},
    )
    assert ver_res.status_code == 200
    assert ver_res.json()["is_verified"] is True
