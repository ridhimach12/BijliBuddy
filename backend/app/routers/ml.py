"""AI/ML endpoints for issue classification, INR price estimation, electrician matching, and model metrics."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.constants import CATEGORY_BY_NAME, LOCALITY_MAP
from app.db.session import get_db
from app.ml.issue_classifier import get_issue_classifier
from app.ml.matching_engine import MatchingWeights, rank_electricians
from app.ml.price_estimator import get_price_estimator
from app.schemas.ml import IssueAnalyzeRequest, MatchElectriciansRequest, PriceEstimateRequest
from app.services.electrician_stats import (
    build_electrician_reliability_and_candidate,
    compute_electrician_metrics_map,
    load_active_electrician_profiles,
)

router = APIRouter(prefix="/api/ml", tags=["AI & ML Engine"])


@router.post("/analyze-issue")
def analyze_issue(payload: IssueAnalyzeRequest):
    """Classify free-text electrical problem, run safety hazard check, and compute initial ML price estimate."""
    classifier = get_issue_classifier()
    pricer = get_price_estimator()

    try:
        clf_out = classifier.predict(payload.description, urgency=payload.urgency)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    loc_info = LOCALITY_MAP.get(payload.locality)
    zone = payload.zone or (loc_info["zone"] if loc_info else "Central Delhi")
    complexity = payload.repair_complexity or clf_out["suggested_complexity"]

    price_out = pricer.estimate_price(
        service_category=clf_out["predicted_category"],
        repair_complexity=complexity,
        location_zone=zone,
        urgency=payload.urgency,
        time_of_service=payload.time_of_service,
        estimated_duration=clf_out["estimated_duration_mins"],
    )

    return {
        "classification": clf_out,
        "price_estimate": price_out,
    }


@router.post("/estimate-price")
def estimate_price(payload: PriceEstimateRequest):
    """Run Random Forest Regressor price estimation for chosen category/complexity/zone/urgency."""
    pricer = get_price_estimator()
    cat_meta = CATEGORY_BY_NAME.get(payload.service_category)
    duration = payload.estimated_duration or (
        cat_meta["estimated_duration_mins"] if cat_meta else 45
    )
    return pricer.estimate_price(
        service_category=payload.service_category,
        repair_complexity=payload.repair_complexity,
        location_zone=payload.location_zone,
        urgency=payload.urgency,
        time_of_service=payload.time_of_service,
        estimated_duration=duration,
    )


@router.post("/match-electricians")
def match_electricians(payload: MatchElectriciansRequest, db: Session = Depends(get_db)):
    """Rank top 5 eligible nearby electricians using Haversine distance & explainable weights."""
    profiles = load_active_electrician_profiles(db)
    stats_map = compute_electrician_metrics_map(db)

    candidates = []
    for p in profiles:
        _rel, candidate, _counts = build_electrician_reliability_and_candidate(p, stats_map)
        candidates.append(candidate)

    weights = None
    if payload.weights:
        weights = MatchingWeights(
            distance=payload.weights.distance,
            skill=payload.weights.skill,
            rating=payload.weights.rating,
            acceptance_rate=payload.weights.acceptance_rate,
            completion_rate=payload.weights.completion_rate,
            eta=payload.weights.eta,
        )

    return rank_electricians(
        candidates=candidates,
        customer_lat=payload.latitude,
        customer_lon=payload.longitude,
        target_category=payload.service_category,
        urgency=payload.urgency,
        top_k=payload.top_k,
        weights=weights,
    )


@router.get("/model-metrics")
def get_model_metrics():
    """Return held-out evaluation metrics and transparent synthetic dataset notices for judges."""
    classifier = get_issue_classifier()
    pricer = get_price_estimator()
    return {
        "issue_classifier": classifier.metrics,
        "price_estimator": pricer.metrics,
    }
