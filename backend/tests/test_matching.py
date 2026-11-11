"""Unit tests for Module 2: Intelligent Electrician Matching Engine."""

from app.ml.matching_engine import (
    ElectricianCandidate,
    MatchingWeights,
    haversine_distance_km,
    rank_electricians,
)


def _make_candidate(
    eid: int,
    name: str,
    lat: float,
    lon: float,
    is_available: bool,
    skills: list,
    rating: float = 4.6,
    reviews: int = 20,
    completed: int = 25,
    accepted: int = 28,
    rejected: int = 2,
    verified: str = "verified",
) -> ElectricianCandidate:
    return ElectricianCandidate(
        electrician_id=eid,
        user_id=100 + eid,
        full_name=name,
        phone="+919876543210",
        locality="Saket",
        zone="South Delhi",
        latitude=lat,
        longitude=lon,
        service_radius_km=8.0,
        experience_years=6,
        is_available=is_available,
        working_hours_start="08:00",
        working_hours_end="21:00",
        verification_status=verified,
        base_visit_fee_inr=199,
        skills=skills,
        bio="Experienced technician",
        verified_completed_jobs=completed,
        accepted_jobs=accepted,
        rejected_jobs=rejected,
        cancelled_jobs=1,
        average_rating=rating,
        review_count=reviews,
        on_time_jobs=22,
        on_time_evaluated_jobs=25,
    )


def test_haversine_distance_delhi():
    # Connaught Place (28.6315, 77.2167) to Saket (28.5245, 77.2066) ~ 11.9 km
    dist = haversine_distance_km(28.6315, 77.2167, 28.5245, 77.2066)
    assert 11.0 <= dist <= 13.0
    assert haversine_distance_km(28.5245, 77.2066, 28.5245, 77.2066) == 0.0


def test_unavailable_never_ranked_above_available():
    # Unavailable electrician has perfect location & rating; available one is slightly farther & unverified
    unavailable_pro = _make_candidate(
        1, "Perfect Unavailable", 28.5245, 77.2066, False, ["MCB/circuit breaker"], rating=5.0, reviews=100
    )
    available_junior = _make_candidate(
        2, "Nearby Available", 28.5494, 77.2001, True, ["MCB/circuit breaker"], rating=4.1, reviews=3, verified="pending"
    )
    available_other = _make_candidate(
        3, "Farther Available", 28.5677, 77.2433, True, ["Wiring"], rating=4.3, reviews=10
    )

    result = rank_electricians(
        candidates=[unavailable_pro, available_junior, available_other],
        customer_lat=28.5245,
        customer_lon=77.2066,
        target_category="MCB/circuit breaker",
        urgency="urgent",
        top_k=5,
    )
    recs = result["recommendations"]
    assert len(recs) == 3
    assert recs[0]["electrician_id"] == 2
    assert recs[1]["electrician_id"] == 3
    assert recs[2]["electrician_id"] == 1
    assert recs[2]["is_available"] is False


def test_returns_top_5_with_explanations_and_custom_weights():
    candidates = [
        _make_candidate(
            i,
            f"Electrician {i}",
            28.5245 + (i * 0.005),
            77.2066,
            True,
            ["Wiring"] if i % 2 == 0 else ["Lighting"],
        )
        for i in range(1, 9)
    ]
    weights = MatchingWeights(distance=0.4, skill=0.3, rating=0.1, acceptance_rate=0.1, completion_rate=0.05, eta=0.05)
    result = rank_electricians(
        candidates=candidates,
        customer_lat=28.5245,
        customer_lon=77.2066,
        target_category="Wiring",
        top_k=5,
        weights=weights,
    )
    assert len(result["recommendations"]) == 5
    for rec in result["recommendations"]:
        assert rec["match_score"] > 0
        assert rec["estimated_arrival_mins"] >= 10
        assert len(rec["explanation_reasons"]) >= 3
        assert "feature_breakdown" in rec
