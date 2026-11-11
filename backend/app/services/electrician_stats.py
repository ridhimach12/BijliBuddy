"""Shared aggregation helpers for electrician performance stats, reliability, and matching candidates."""

from typing import Dict, List, Tuple

from sqlalchemy.orm import Session, joinedload

from app.db.models import Booking, ElectricianProfile, ElectricianSkill, Review
from app.ml.matching_engine import ElectricianCandidate
from app.ml.reliability import ReliabilityMetricsInput, compute_reliability_score


def compute_electrician_metrics_map(db: Session) -> Dict[int, Dict]:
    """Aggregate booking and review metrics for all electricians in a single pass."""
    bookings = db.query(Booking).all()
    reviews = db.query(Review).all()

    booking_stats: Dict[int, Dict[str, int]] = {}
    for b in bookings:
        s = booking_stats.setdefault(
            b.electrician_id,
            {
                "completed": 0,
                "accepted": 0,
                "rejected": 0,
                "cancelled": 0,
                "on_time_yes": 0,
                "on_time_total": 0,
                "total_bookings": 0,
                "active": 0,
                "pending": 0,
            },
        )
        s["total_bookings"] += 1
        if b.status == "completed":
            s["completed"] += 1
            s["accepted"] += 1
            if b.on_time_completed is not None:
                s["on_time_total"] += 1
                if b.on_time_completed:
                    s["on_time_yes"] += 1
        elif b.status in ("accepted", "in_progress"):
            s["accepted"] += 1
            s["active"] += 1
        elif b.status == "pending":
            s["pending"] += 1
        elif b.status == "rejected":
            s["rejected"] += 1
        elif b.status == "cancelled":
            # Only count cancellations after electrician accepted, or general discipline tracking
            if b.accepted_at is not None:
                s["cancelled"] += 1
                s["accepted"] += 1

    review_stats: Dict[int, Tuple[float, int]] = {}
    rev_acc: Dict[int, List[int]] = {}
    for r in reviews:
        rev_acc.setdefault(r.electrician_id, []).append(r.rating)
    for eid, ratings in rev_acc.items():
        review_stats[eid] = (sum(ratings) / len(ratings), len(ratings))

    return {"bookings": booking_stats, "reviews": review_stats}


def build_electrician_reliability_and_candidate(
    profile: ElectricianProfile,
    stats_map: Dict[int, Dict],
) -> Tuple[Dict, ElectricianCandidate, Dict]:
    """Compute reliability dict, MatchingEngine candidate, and raw counts for one electrician."""
    b = stats_map["bookings"].get(
        profile.id,
        {
            "completed": 0,
            "accepted": 0,
            "rejected": 0,
            "cancelled": 0,
            "on_time_yes": 0,
            "on_time_total": 0,
            "total_bookings": 0,
            "active": 0,
            "pending": 0,
        },
    )
    avg_rating, rev_count = stats_map["reviews"].get(profile.id, (None, 0))
    skills = [sk.category.name for sk in profile.skills if sk.category is not None]

    rel_input = ReliabilityMetricsInput(
        verified_completed_jobs=b["completed"],
        accepted_jobs=b["accepted"],
        rejected_jobs=b["rejected"],
        cancelled_jobs=b["cancelled"],
        average_rating=avg_rating,
        review_count=rev_count,
        on_time_jobs=b["on_time_yes"],
        on_time_evaluated_jobs=b["on_time_total"],
        is_admin_verified=(profile.verification_status == "verified"),
    )
    reliability = compute_reliability_score(rel_input)

    candidate = ElectricianCandidate(
        electrician_id=profile.id,
        user_id=profile.user_id,
        full_name=profile.user.full_name,
        phone=profile.user.phone,
        locality=profile.locality,
        zone=profile.zone,
        latitude=profile.latitude,
        longitude=profile.longitude,
        service_radius_km=profile.service_radius_km,
        experience_years=profile.experience_years,
        is_available=profile.is_available,
        working_hours_start=profile.working_hours_start,
        working_hours_end=profile.working_hours_end,
        verification_status=profile.verification_status,
        base_visit_fee_inr=profile.base_visit_fee_inr,
        skills=skills,
        bio=profile.bio,
        verified_completed_jobs=b["completed"],
        accepted_jobs=b["accepted"],
        rejected_jobs=b["rejected"],
        cancelled_jobs=b["cancelled"],
        average_rating=avg_rating,
        review_count=rev_count,
        on_time_jobs=b["on_time_yes"],
        on_time_evaluated_jobs=b["on_time_total"],
    )
    return reliability, candidate, b


def load_active_electrician_profiles(db: Session) -> List[ElectricianProfile]:
    """Fetch all active electrician profiles with user and skill categories eager-loaded."""
    return (
        db.query(ElectricianProfile)
        .join(ElectricianProfile.user)
        .options(
            joinedload(ElectricianProfile.user),
            joinedload(ElectricianProfile.skills).joinedload(ElectricianSkill.category),
        )
        .filter(ElectricianProfile.user.has(is_active=True))
        .all()
    )
