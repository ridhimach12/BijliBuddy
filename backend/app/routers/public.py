"""Public discovery endpoints (categories, Delhi localities, electrician directory, notifications)."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.constants import DELHI_LOCALITIES, EMERGENCY_HELPLINES
from app.core.security import get_current_user
from app.db.models import ElectricianProfile, Notification, Review, ServiceCategory, User
from app.db.session import get_db
from app.services.electrician_stats import (
    build_electrician_reliability_and_candidate,
    compute_electrician_metrics_map,
    load_active_electrician_profiles,
)

router = APIRouter(prefix="/api/public", tags=["Public & Discovery"])


@router.get("/categories")
def list_categories(db: Session = Depends(get_db)):
    """List all supported electrical service categories."""
    cats = db.query(ServiceCategory).order_by(ServiceCategory.id.asc()).all()
    return {
        "categories": [
            {
                "id": c.id,
                "name": c.name,
                "slug": c.slug,
                "description": c.description,
                "base_price_inr": c.base_price_inr,
                "estimated_duration_mins": c.estimated_duration_mins,
                "safety_level": c.safety_level,
                "icon_name": c.icon_name,
            }
            for c in cats
        ]
    }


@router.get("/localities")
def list_localities():
    """Return Delhi service localities with coordinates, zone, and emergency helplines."""
    return {
        "city": "New Delhi",
        "localities": DELHI_LOCALITIES,
        "emergency_helplines": EMERGENCY_HELPLINES,
    }


@router.get("/electricians")
def browse_electricians(
    locality: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    verified_only: bool = Query(default=False),
    available_only: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    """Browse active electricians with reliability scores and verification status."""
    profiles = load_active_electrician_profiles(db)
    stats_map = compute_electrician_metrics_map(db)

    items = []
    for p in profiles:
        if locality and p.locality.lower() != locality.lower():
            continue
        if verified_only and p.verification_status != "verified":
            continue
        if available_only and not p.is_available:
            continue

        skills = [sk.category.name for sk in p.skills if sk.category]
        if category and category not in skills:
            continue

        reliability, candidate, raw_counts = build_electrician_reliability_and_candidate(p, stats_map)
        items.append(
            {
                "id": p.id,
                "user_id": p.user_id,
                "full_name": p.user.full_name,
                "locality": p.locality,
                "zone": p.zone,
                "latitude": p.latitude,
                "longitude": p.longitude,
                "experience_years": p.experience_years,
                "service_radius_km": p.service_radius_km,
                "is_available": p.is_available,
                "working_hours": f"{p.working_hours_start} - {p.working_hours_end}",
                "verification_status": p.verification_status,
                "is_verified": p.verification_status == "verified",
                "base_visit_fee_inr": p.base_visit_fee_inr,
                "bio": p.bio,
                "skills": skills,
                "reliability_score": reliability["reliability_score"],
                "reliability_tier": reliability["confidence_tier"],
                "average_rating": reliability["raw_average_rating"],
                "smoothed_rating": reliability["smoothed_rating"],
                "review_count": reliability["review_count"],
                "completed_jobs": raw_counts["completed"],
                "is_demo": p.user.is_demo,
            }
        )

    items.sort(key=lambda x: (1 if x["is_available"] else 0, x["reliability_score"]), reverse=True)
    return {"total": len(items), "electricians": items}


@router.get("/electricians/{electrician_id}")
def get_electrician_public_profile(electrician_id: int, db: Session = Depends(get_db)):
    """Get full public profile, explainable reliability breakdown, availability, and reviews."""
    profile = db.query(ElectricianProfile).filter(ElectricianProfile.id == electrician_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Electrician not found.")

    stats_map = compute_electrician_metrics_map(db)
    reliability, _candidate, raw_counts = build_electrician_reliability_and_candidate(profile, stats_map)
    reviews = (
        db.query(Review)
        .filter(Review.electrician_id == profile.id)
        .order_by(Review.created_at.desc())
        .limit(20)
        .all()
    )

    reviewer_ids = [r.customer_id for r in reviews]
    users_map = (
        {u.id: u.full_name for u in db.query(User).filter(User.id.in_(reviewer_ids)).all()}
        if reviewer_ids
        else {}
    )

    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "full_name": profile.user.full_name,
        "phone": profile.user.phone,
        "locality": profile.locality,
        "zone": profile.zone,
        "address": profile.address,
        "latitude": profile.latitude,
        "longitude": profile.longitude,
        "experience_years": profile.experience_years,
        "service_radius_km": profile.service_radius_km,
        "is_available": profile.is_available,
        "working_hours_start": profile.working_hours_start,
        "working_hours_end": profile.working_hours_end,
        "verification_status": profile.verification_status,
        "is_verified": profile.verification_status == "verified",
        "credential_id": profile.credential_id if profile.verification_status == "verified" else None,
        "base_visit_fee_inr": profile.base_visit_fee_inr,
        "bio": profile.bio,
        "is_demo": profile.user.is_demo,
        "skills": [sk.category.name for sk in profile.skills if sk.category],
        "availability_slots": [
            {
                "day_of_week": slot.day_of_week,
                "start_time": slot.start_time,
                "end_time": slot.end_time,
                "is_active": slot.is_active,
            }
            for slot in sorted(profile.availability_slots, key=lambda s: s.day_of_week)
        ],
        "stats": raw_counts,
        "reliability": reliability,
        "reviews": [
            {
                "id": r.id,
                "customer_name": users_map.get(r.customer_id, "Household Customer"),
                "rating": r.rating,
                "comment": r.comment,
                "was_on_time": r.was_on_time,
                "created_at": r.created_at.isoformat(),
            }
            for r in reviews
        ],
    }


@router.get("/notifications")
def list_my_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetch recent notifications for polling updates."""
    notifs = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(20)
        .all()
    )
    unread_count = sum(1 for n in notifs if not n.is_read)
    return {
        "unread_count": unread_count,
        "notifications": [
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "type": n.type,
                "related_booking_id": n.related_booking_id,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat(),
            }
            for n in notifs
        ],
    }


@router.post("/notifications/read-all")
def mark_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark all unread notifications as read for current user."""
    db.query(Notification).filter(
        Notification.user_id == current_user.id, Notification.is_read == False  # noqa: E712
    ).update({"is_read": True})
    db.commit()
    return {"status": "ok"}
