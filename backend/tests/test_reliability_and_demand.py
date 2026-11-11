"""Unit tests for Module 4 (Demand Analytics) & Module 5 (Reliability Score)."""

from datetime import datetime, timedelta, timezone

from app.ml.demand_analytics import analyze_and_forecast_demand
from app.ml.reliability import ReliabilityMetricsInput, compute_reliability_score


def test_reliability_bayesian_fairness_for_new_electricians():
    new_worker = compute_reliability_score(
        ReliabilityMetricsInput(
            verified_completed_jobs=0,
            accepted_jobs=0,
            rejected_jobs=0,
            cancelled_jobs=0,
            average_rating=None,
            review_count=0,
            on_time_jobs=0,
            on_time_evaluated_jobs=0,
            is_admin_verified=False,
        )
    )
    # Fair neutral baseline score (~75-85) instead of 0
    assert new_worker["reliability_score"] >= 70.0
    assert "Provisional" in new_worker["confidence_tier"]
    assert new_worker["is_admin_verified"] is False

    veteran = compute_reliability_score(
        ReliabilityMetricsInput(
            verified_completed_jobs=40,
            accepted_jobs=42,
            rejected_jobs=2,
            cancelled_jobs=1,
            average_rating=4.85,
            review_count=35,
            on_time_jobs=38,
            on_time_evaluated_jobs=40,
            is_admin_verified=True,
        )
    )
    assert veteran["reliability_score"] > new_worker["reliability_score"]
    assert veteran["is_admin_verified"] is True
    assert veteran["confidence_tier"] == "Established Track Record"


def test_demand_analytics_and_forecasting():
    base = datetime(2026, 10, 15, 10, 0, tzinfo=timezone.utc)
    records = []
    for day_offset in range(14):
        records.append(
            {
                "locality": "Saket" if day_offset % 2 == 0 else "Dwarka",
                "category": "MCB/circuit breaker" if day_offset % 3 == 0 else "Wiring",
                "time_slot": "Morning (6AM-12PM)" if day_offset % 2 == 0 else "Evening (5PM-9PM)",
                "created_at": (base + timedelta(days=day_offset)).isoformat(),
            }
        )
    out = analyze_and_forecast_demand(records, forecast_horizon_days=7)
    assert out["total_analyzed_bookings"] == 14
    assert len(out["forecast_next_days"]) == 7
    assert len(out["by_locality"]) == 2
    assert len(out["model_info"]["limitations"]) >= 2
    for day in out["forecast_next_days"]:
        assert day["lower_bound"] <= day["expected_bookings"] <= day["upper_bound"]
