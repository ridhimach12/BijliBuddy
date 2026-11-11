"""Electrician endpoints: profile, availability, incoming requests, active/completed jobs, earnings."""

from collections import defaultdict
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.constants import CATEGORY_NAMES, LOCALITY_MAP
from app.core.security import require_role
from app.db.models import (
    Availability,
    Booking,
    ElectricianProfile,
    ElectricianSkill,
    Payment,
    Review,
    ServiceCategory,
    User,
)
from app.db.session import get_db
from app.schemas.booking import BookingAcceptRejectRequest, BookingStatusActionRequest
from app.schemas.user import ElectricianProfileUpdate
from app.services.booking_service import serialize_booking
from app.services.electrician_stats import (
    build_electrician_reliability_and_candidate,
    compute_electrician_metrics_map,
)
from app.services.notifications import create_notification

router = APIRouter(prefix="/api/electricians", tags=["Electricians"])


def _get_owned_profile(user: User, db: Session) -> ElectricianProfile:
    profile = (
        db.query(ElectricianProfile)
        .options(
            joinedload(ElectricianProfile.user),
            joinedload(ElectricianProfile.skills).joinedload(ElectricianSkill.category),
            joinedload(ElectricianProfile.availability_slots),
        )
        .filter(ElectricianProfile.user_id == user.id)
        .first()
    )
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Electrician profile not found.")
    return profile


@router.get("/profile")
def get_my_electrician_profile(
    current_user: User = Depends(require_role("electrician")),
    db: Session = Depends(get_db),
):
    """Get authenticated electrician's profile, skills, availability, and reliability score."""
    profile = _get_owned_profile(current_user, db)
    stats_map = compute_electrician_metrics_map(db)
    reliability, _cand, raw_counts = build_electrician_reliability_and_candidate(profile, stats_map)

    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "phone": current_user.phone,
        "is_demo": current_user.is_demo,
        "bio": profile.bio,
        "experience_years": profile.experience_years,
        "service_radius_km": profile.service_radius_km,
        "locality": profile.locality,
        "zone": profile.zone,
        "address": profile.address,
        "latitude": profile.latitude,
        "longitude": profile.longitude,
        "is_available": profile.is_available,
        "working_hours_start": profile.working_hours_start,
        "working_hours_end": profile.working_hours_end,
        "verification_status": profile.verification_status,
        "is_verified": profile.verification_status == "verified",
        "credential_id": profile.credential_id,
        "verification_notes": profile.verification_notes,
        "base_visit_fee_inr": profile.base_visit_fee_inr,
        "total_earnings_inr": profile.total_earnings_inr,
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
    }


@router.put("/profile")
def update_my_electrician_profile(
    payload: ElectricianProfileUpdate,
    current_user: User = Depends(require_role("electrician")),
    db: Session = Depends(get_db),
):
    """Update electrician skills, radius, availability, working hours, and credential submission."""
    profile = _get_owned_profile(current_user, db)

    if payload.full_name is not None:
        current_user.full_name = payload.full_name.strip()
    if payload.phone is not None:
        current_user.phone = payload.phone
    if payload.bio is not None:
        profile.bio = payload.bio.strip()
    if payload.experience_years is not None:
        profile.experience_years = payload.experience_years
    if payload.service_radius_km is not None:
        profile.service_radius_km = payload.service_radius_km
    if payload.locality is not None:
        loc_info = LOCALITY_MAP.get(payload.locality)
        profile.locality = payload.locality
        if loc_info:
            profile.zone = loc_info["zone"]
            if payload.latitude is None and payload.longitude is None:
                profile.latitude = loc_info["latitude"]
                profile.longitude = loc_info["longitude"]
    if payload.address is not None:
        profile.address = payload.address.strip()
    if payload.latitude is not None:
        profile.latitude = payload.latitude
    if payload.longitude is not None:
        profile.longitude = payload.longitude
    if payload.is_available is not None:
        profile.is_available = payload.is_available
    if payload.working_hours_start is not None:
        profile.working_hours_start = payload.working_hours_start
    if payload.working_hours_end is not None:
        profile.working_hours_end = payload.working_hours_end
    if payload.base_visit_fee_inr is not None:
        profile.base_visit_fee_inr = payload.base_visit_fee_inr

    # Credential submission sets status to pending unless already verified with same ID;
    # electricians can NEVER self-verify.
    if payload.credential_id is not None:
        cleaned_cred = payload.credential_id.strip() or None
        if cleaned_cred != profile.credential_id:
            profile.credential_id = cleaned_cred
            profile.verification_status = "pending" if cleaned_cred else "unverified"
            profile.verified_by_admin_id = None
            profile.verified_at = None

    if payload.skills is not None:
        valid_skills = [s for s in payload.skills if s in CATEGORY_NAMES]
        db.query(ElectricianSkill).filter(ElectricianSkill.electrician_id == profile.id).delete()
        cats = db.query(ServiceCategory).filter(ServiceCategory.name.in_(valid_skills)).all()
        for cat in cats:
            db.add(
                ElectricianSkill(
                    electrician_id=profile.id,
                    category_id=cat.id,
                    proficiency_level="expert" if profile.experience_years >= 5 else "intermediate",
                    years_experience=max(1, profile.experience_years),
                )
            )

    if payload.availability_slots is not None:
        db.query(Availability).filter(Availability.electrician_id == profile.id).delete()
        for slot in payload.availability_slots:
            db.add(
                Availability(
                    electrician_id=profile.id,
                    day_of_week=slot.day_of_week,
                    start_time=slot.start_time,
                    end_time=slot.end_time,
                    is_active=slot.is_active,
                )
            )

    db.commit()
    return get_my_electrician_profile(current_user=current_user, db=db)


@router.get("/dashboard")
def get_electrician_dashboard(
    current_user: User = Depends(require_role("electrician")),
    db: Session = Depends(get_db),
):
    """Comprehensive electrician workspace: incoming, active, completed jobs, earnings, and reviews."""
    profile = _get_owned_profile(current_user, db)
    stats_map = compute_electrician_metrics_map(db)
    reliability, _cand, raw_counts = build_electrician_reliability_and_candidate(profile, stats_map)

    bookings = (
        db.query(Booking)
        .options(
            joinedload(Booking.service_request),
            joinedload(Booking.customer),
            joinedload(Booking.electrician).joinedload(ElectricianProfile.user),
            joinedload(Booking.review),
            joinedload(Booking.payment),
        )
        .filter(Booking.electrician_id == profile.id)
        .order_by(Booking.created_at.desc())
        .all()
    )

    serialized = [serialize_booking(b) for b in bookings]
    incoming = [b for b in serialized if b["status"] == "pending"]
    active = [b for b in serialized if b["status"] in ("accepted", "in_progress")]
    completed = [b for b in serialized if b["status"] == "completed"]
    history = [b for b in serialized if b["status"] in ("completed", "rejected", "cancelled")]

    # Earnings breakdowns by category and by date for Recharts
    earnings_by_category = defaultdict(float)
    earnings_by_date = defaultdict(float)
    for b in bookings:
        if b.status == "completed":
            amt = float(b.final_amount_inr or b.electrician_quote_inr or b.ai_estimate_snapshot_inr or 0.0)
            cat_name = b.service_request.selected_category if b.service_request else "General"
            earnings_by_category[cat_name] += amt
            dt_key = (b.completed_at or b.created_at).date().isoformat()
            earnings_by_date[dt_key] += amt

    reviews = (
        db.query(Review)
        .filter(Review.electrician_id == profile.id)
        .order_by(Review.created_at.desc())
        .all()
    )
    cust_ids = [r.customer_id for r in reviews]
    cust_map = (
        {u.id: u.full_name for u in db.query(User).filter(User.id.in_(cust_ids)).all()}
        if cust_ids
        else {}
    )

    return {
        "profile": get_my_electrician_profile(current_user=current_user, db=db),
        "reliability": reliability,
        "counts": {
            "incoming_requests": len(incoming),
            "active_jobs": len(active),
            "completed_jobs": len(completed),
            "rejected_jobs": raw_counts["rejected"],
        },
        "incoming_requests": incoming,
        "active_jobs": active,
        "completed_jobs": completed,
        "job_history": history,
        "earnings": {
            "total_earnings_inr": round(float(profile.total_earnings_inr), 2),
            "average_job_value_inr": round(
                float(profile.total_earnings_inr) / len(completed), 2
            )
            if completed
            else 0.0,
            "by_category": [
                {"category": k, "earnings_inr": round(v, 2)}
                for k, v in sorted(earnings_by_category.items(), key=lambda x: -x[1])
            ],
            "by_date": [
                {"date": k, "earnings_inr": round(v, 2)}
                for k, v in sorted(earnings_by_date.items())
            ],
        },
        "reviews": [
            {
                "id": r.id,
                "booking_id": r.booking_id,
                "customer_name": cust_map.get(r.customer_id, "Household Customer"),
                "rating": r.rating,
                "comment": r.comment,
                "was_on_time": r.was_on_time,
                "created_at": r.created_at.isoformat(),
            }
            for r in reviews
        ],
    }


@router.post("/bookings/{booking_id}/respond")
def respond_to_booking(
    booking_id: int,
    payload: BookingAcceptRejectRequest,
    current_user: User = Depends(require_role("electrician")),
    db: Session = Depends(get_db),
):
    """Electrician accepts (with optional quotation) or rejects an incoming booking request."""
    profile = _get_owned_profile(current_user, db)
    booking = (
        db.query(Booking)
        .options(joinedload(Booking.service_request), joinedload(Booking.customer))
        .filter(Booking.id == booking_id, Booking.electrician_id == profile.id)
        .first()
    )
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found.")
    if booking.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot respond to booking in '{booking.status}' state.",
        )

    now = datetime.now(timezone.utc)
    if payload.action == "accept":
        booking.status = "accepted"
        booking.accepted_at = now
        booking.electrician_quote_inr = (
            payload.electrician_quote_inr
            if payload.electrician_quote_inr is not None
            else booking.ai_estimate_snapshot_inr
        )
        booking.electrician_notes = payload.electrician_notes
        create_notification(
            db,
            user_id=booking.customer_id,
            title="Booking Accepted!",
            message=(
                f"{current_user.full_name} accepted booking #{booking.id} "
                f"(Quoted: ₹{booking.electrician_quote_inr:.0f}, ETA ~{booking.estimated_arrival_mins} mins)."
            ),
            notif_type="booking_update",
            related_booking_id=booking.id,
        )
    else:
        booking.status = "rejected"
        booking.electrician_notes = payload.electrician_notes or "Unavailable for this slot."
        create_notification(
            db,
            user_id=booking.customer_id,
            title="Booking Declined",
            message=f"{current_user.full_name} could not accept booking #{booking.id}. Please choose another nearby electrician.",
            notif_type="booking_update",
            related_booking_id=booking.id,
        )

    db.commit()
    db.refresh(booking)
    return {"booking": serialize_booking(booking)}


@router.post("/bookings/{booking_id}/start")
def start_booking_job(
    booking_id: int,
    current_user: User = Depends(require_role("electrician")),
    db: Session = Depends(get_db),
):
    """Transition an accepted booking to in_progress."""
    profile = _get_owned_profile(current_user, db)
    booking = (
        db.query(Booking)
        .filter(Booking.id == booking_id, Booking.electrician_id == profile.id)
        .first()
    )
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found.")
    if booking.status != "accepted":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only accepted bookings can be marked in progress.",
        )

    booking.status = "in_progress"
    booking.started_at = datetime.now(timezone.utc)
    create_notification(
        db,
        user_id=booking.customer_id,
        title="Work Started",
        message=f"{current_user.full_name} has arrived and started work on booking #{booking.id}.",
        notif_type="booking_update",
        related_booking_id=booking.id,
    )
    db.commit()
    db.refresh(booking)
    return {"booking": serialize_booking(booking)}


@router.post("/bookings/{booking_id}/complete")
def complete_booking_job(
    booking_id: int,
    payload: BookingStatusActionRequest,
    current_user: User = Depends(require_role("electrician")),
    db: Session = Depends(get_db),
):
    """Mark an accepted/in_progress booking as completed and update electrician earnings."""
    profile = _get_owned_profile(current_user, db)
    booking = (
        db.query(Booking)
        .options(joinedload(Booking.payment))
        .filter(Booking.id == booking_id, Booking.electrician_id == profile.id)
        .first()
    )
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found.")
    if booking.status not in ("accepted", "in_progress"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only accepted or in-progress jobs can be marked completed.",
        )

    final_amt = float(
        payload.final_amount_inr
        or booking.electrician_quote_inr
        or booking.ai_estimate_snapshot_inr
    )
    booking.status = "completed"
    booking.completed_at = datetime.now(timezone.utc)
    booking.final_amount_inr = final_amt
    booking.on_time_completed = True if payload.on_time_completed is None else payload.on_time_completed
    if payload.electrician_notes:
        booking.electrician_notes = payload.electrician_notes

    profile.total_earnings_inr = round(float(profile.total_earnings_inr) + final_amt, 2)

    if booking.payment is None:
        db.add(
            Payment(
                booking_id=booking.id,
                customer_id=booking.customer_id,
                amount_inr=final_amt,
                payment_method="sandbox_upi",
                status="pending",
                is_sandbox=True,
                transaction_ref=f"DEMO-INV-{booking.id}",
            )
        )

    create_notification(
        db,
        user_id=booking.customer_id,
        title="Job Completed — Please Rate & Review",
        message=f"Booking #{booking.id} completed by {current_user.full_name} (Final amount: ₹{final_amt:.0f}).",
        notif_type="booking_update",
        related_booking_id=booking.id,
    )
    db.commit()
    db.refresh(booking)
    return {"booking": serialize_booking(booking)}
