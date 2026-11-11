"""Admin endpoints: platform KPIs, demand analytics & forecasting, leaderboard, and credential verification."""

from collections import defaultdict
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.security import require_role
from app.db.models import Booking, ElectricianProfile, ServiceRequest, User
from app.db.session import get_db
from app.ml.demand_analytics import analyze_and_forecast_demand
from app.schemas.admin import VerificationDecisionRequest
from app.services.electrician_stats import (
    build_electrician_reliability_and_candidate,
    compute_electrician_metrics_map,
    load_active_electrician_profiles,
)
from app.services.notifications import create_notification

router = APIRouter(prefix="/api/admin", tags=["Admin Analytics & Governance"])


@router.get("/overview")
def get_admin_overview(
    _admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Return real-time platform KPIs, booking trends, geographic demand, and category distribution."""
    total_customers = db.query(User).filter(User.role == "customer").count()
    electricians = db.query(ElectricianProfile).all()
    total_electricians = len(electricians)
    verified_electricians = sum(1 for e in electricians if e.verification_status == "verified")
    pending_verifications = sum(1 for e in electricians if e.verification_status == "pending")

    bookings = (
        db.query(Booking)
        .options(joinedload(Booking.service_request))
        .all()
    )
    total_bookings = len(bookings)
    completed_bookings = sum(1 for b in bookings if b.status == "completed")
    cancelled_bookings = sum(1 for b in bookings if b.status == "cancelled")
    rejected_bookings = sum(1 for b in bookings if b.status == "rejected")
    active_bookings = sum(1 for b in bookings if b.status in ("pending", "accepted", "in_progress"))

    cancellation_rate = (
        round((cancelled_bookings / total_bookings) * 100.0, 1) if total_bookings > 0 else 0.0
    )

    realized_revenue = sum(
        float(b.final_amount_inr or b.electrician_quote_inr or b.ai_estimate_snapshot_inr or 0.0)
        for b in bookings
        if b.status == "completed"
    )
    pipeline_revenue = sum(
        float(b.electrician_quote_inr or b.ai_estimate_snapshot_inr or 0.0)
        for b in bookings
        if b.status in ("pending", "accepted", "in_progress")
    )

    # Trends by date, locality, and category
    daily_counts = defaultdict(lambda: {"bookings": 0, "completed": 0, "revenue_inr": 0.0})
    locality_counts = defaultdict(int)
    category_counts = defaultdict(int)
    status_counts = defaultdict(int)

    for b in bookings:
        status_counts[b.status] += 1
        d_key = b.created_at.date().isoformat()
        daily_counts[d_key]["bookings"] += 1
        if b.status == "completed":
            daily_counts[d_key]["completed"] += 1
            daily_counts[d_key]["revenue_inr"] += float(
                b.final_amount_inr or b.electrician_quote_inr or b.ai_estimate_snapshot_inr or 0.0
            )
        if b.service_request:
            locality_counts[b.service_request.locality] += 1
            category_counts[b.service_request.selected_category] += 1

    return {
        "kpis": {
            "total_customers": total_customers,
            "registered_electricians": total_electricians,
            "verified_electricians": verified_electricians,
            "pending_verifications": pending_verifications,
            "total_bookings": total_bookings,
            "completed_bookings": completed_bookings,
            "active_bookings": active_bookings,
            "cancelled_bookings": cancelled_bookings,
            "rejected_bookings": rejected_bookings,
            "cancellation_rate_pct": cancellation_rate,
            "realized_revenue_inr": round(realized_revenue, 2),
            "estimated_pipeline_revenue_inr": round(pipeline_revenue, 2),
        },
        "status_breakdown": [
            {"status": k, "count": v} for k, v in status_counts.items()
        ],
        "booking_trends": [
            {"date": k, **v} for k, v in sorted(daily_counts.items())
        ],
        "geographic_distribution": [
            {"locality": k, "bookings": v}
            for k, v in sorted(locality_counts.items(), key=lambda x: -x[1])
        ],
        "category_distribution": [
            {"category": k, "bookings": v}
            for k, v in sorted(category_counts.items(), key=lambda x: -x[1])
        ],
    }


@router.get("/demand-analytics")
def get_admin_demand_analytics(
    horizon_days: int = 7,
    _admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Run Module 4 demand analytics and statistical short-term demand forecasting."""
    bookings = (
        db.query(Booking)
        .options(joinedload(Booking.service_request))
        .all()
    )
    records = []
    for b in bookings:
        records.append(
            {
                "locality": b.service_request.locality if b.service_request else "Unknown",
                "category": b.service_request.selected_category if b.service_request else "General electrical maintenance",
                "time_slot": b.time_slot_bucket,
                "created_at": b.created_at.isoformat(),
            }
        )
    return analyze_and_forecast_demand(records, forecast_horizon_days=min(14, max(3, horizon_days)))


@router.get("/leaderboard")
def get_electrician_leaderboard(
    _admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Return electrician performance leaderboard ranked by Bayesian Reliability Score."""
    profiles = load_active_electrician_profiles(db)
    stats_map = compute_electrician_metrics_map(db)

    board = []
    for p in profiles:
        rel, _cand, raw = build_electrician_reliability_and_candidate(p, stats_map)
        board.append(
            {
                "electrician_id": p.id,
                "full_name": p.user.full_name,
                "locality": p.locality,
                "zone": p.zone,
                "verification_status": p.verification_status,
                "is_verified": p.verification_status == "verified",
                "is_available": p.is_available,
                "experience_years": p.experience_years,
                "reliability_score": rel["reliability_score"],
                "confidence_tier": rel["confidence_tier"],
                "completed_jobs": raw["completed"],
                "accepted_jobs": raw["accepted"],
                "rejected_jobs": raw["rejected"],
                "cancelled_jobs": raw["cancelled"],
                "acceptance_rate_pct": round(rel["smoothed_acceptance_rate"] * 100.0, 1),
                "average_rating": rel["raw_average_rating"],
                "smoothed_rating": rel["smoothed_rating"],
                "review_count": rel["review_count"],
                "total_earnings_inr": round(float(p.total_earnings_inr), 2),
                "skills": [sk.category.name for sk in p.skills if sk.category],
            }
        )

    board.sort(key=lambda x: (x["reliability_score"], x["completed_jobs"]), reverse=True)
    return {"leaderboard": board}


@router.get("/electricians")
def list_electricians_for_verification(
    _admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """List all registered electricians and credential verification details for Admin review."""
    profiles = load_active_electrician_profiles(db)
    return {
        "electricians": [
            {
                "id": p.id,
                "user_id": p.user_id,
                "full_name": p.user.full_name,
                "email": p.user.email,
                "phone": p.user.phone,
                "locality": p.locality,
                "zone": p.zone,
                "experience_years": p.experience_years,
                "credential_id": p.credential_id,
                "verification_status": p.verification_status,
                "verification_notes": p.verification_notes,
                "verified_at": p.verified_at.isoformat() if p.verified_at else None,
                "is_demo": p.user.is_demo,
                "skills": [sk.category.name for sk in p.skills if sk.category],
            }
            for p in sorted(
                profiles,
                key=lambda x: (0 if x.verification_status == "pending" else 1, -x.id),
            )
        ]
    }


@router.post("/electricians/{electrician_id}/verify")
def verify_electrician_credentials(
    electrician_id: int,
    payload: VerificationDecisionRequest,
    admin_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """Explicit Admin approval/rejection of an electrician's identity and license credentials."""
    profile = (
        db.query(ElectricianProfile)
        .options(joinedload(ElectricianProfile.user))
        .filter(ElectricianProfile.id == electrician_id)
        .first()
    )
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Electrician not found.")

    if payload.decision == "verified" and not profile.credential_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot mark electrician verified without a submitted credential ID.",
        )

    profile.verification_status = payload.decision
    profile.verification_notes = payload.verification_notes or f"Reviewed by {admin_user.full_name}"
    if payload.decision == "verified":
        profile.verified_by_admin_id = admin_user.id
        profile.verified_at = datetime.now(timezone.utc)
    else:
        profile.verified_by_admin_id = None
        profile.verified_at = None

    create_notification(
        db,
        user_id=profile.user_id,
        title=f"Verification Status Updated: {payload.decision.title()}",
        message=f"Admin review result: {profile.verification_status}. {profile.verification_notes or ''}",
        notif_type="verification",
    )
    db.commit()
    db.refresh(profile)
    return {
        "electrician_id": profile.id,
        "verification_status": profile.verification_status,
        "is_verified": profile.verification_status == "verified",
        "verified_at": profile.verified_at.isoformat() if profile.verified_at else None,
        "verification_notes": profile.verification_notes,
    }
