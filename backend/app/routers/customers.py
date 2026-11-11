"""Customer endpoints: profile, image upload, service requests, bookings, and reviews."""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.core.constants import CATEGORY_BY_NAME, LOCALITY_MAP
from app.core.security import require_role
from app.db.models import (
    Booking,
    CustomerProfile,
    ElectricianProfile,
    Review,
    ServiceRequest,
    User,
)
from app.db.session import get_db
from app.ml.issue_classifier import get_issue_classifier
from app.ml.matching_engine import estimate_arrival_minutes, haversine_distance_km, rank_electricians
from app.ml.price_estimator import get_price_estimator
from app.schemas.booking import BookingCreate, ReviewCreateRequest, ServiceRequestCreate
from app.schemas.user import CustomerProfileUpdate
from app.services.booking_service import serialize_booking
from app.services.electrician_stats import (
    build_electrician_reliability_and_candidate,
    compute_electrician_metrics_map,
    load_active_electrician_profiles,
)
from app.services.notifications import create_notification
from app.services.safety import IMAGE_UPLOAD_DISCLAIMER

router = APIRouter(prefix="/api/customers", tags=["Customers"])
ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


@router.get("/profile")
def get_customer_profile(
    current_user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db),
):
    """Get authenticated customer's profile."""
    profile = db.query(CustomerProfile).filter(CustomerProfile.user_id == current_user.id).first()
    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "phone": current_user.phone,
        "is_demo": current_user.is_demo,
        "address": profile.address if profile else "",
        "locality": profile.locality if profile else "Saket",
        "zone": profile.zone if profile else "South Delhi",
        "latitude": profile.latitude if profile else 28.5245,
        "longitude": profile.longitude if profile else 77.2066,
    }


@router.put("/profile")
def update_customer_profile(
    payload: CustomerProfileUpdate,
    current_user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db),
):
    """Update customer profile and default locality/address."""
    profile = db.query(CustomerProfile).filter(CustomerProfile.user_id == current_user.id).first()
    if not profile:
        profile = CustomerProfile(user_id=current_user.id)
        db.add(profile)

    if payload.full_name is not None:
        current_user.full_name = payload.full_name.strip()
    if payload.phone is not None:
        current_user.phone = payload.phone
    if payload.address is not None:
        profile.address = payload.address.strip()
    if payload.locality is not None:
        loc_info = LOCALITY_MAP.get(payload.locality)
        profile.locality = payload.locality
        if loc_info:
            profile.zone = loc_info["zone"]
            if payload.latitude is None and payload.longitude is None:
                profile.latitude = loc_info["latitude"]
                profile.longitude = loc_info["longitude"]
    if payload.latitude is not None:
        profile.latitude = payload.latitude
    if payload.longitude is not None:
        profile.longitude = payload.longitude

    db.commit()
    db.refresh(profile)
    return get_customer_profile(current_user=current_user, db=db)


@router.post("/upload-image")
async def upload_issue_image(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role("customer")),
):
    """Upload optional reference photo for the electrician (never AI-diagnosed)."""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Upload JPG, JPEG, PNG, or WEBP.",
        )

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image size exceeds 5 MB limit.",
        )

    settings = get_settings()
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"req_{current_user.id}_{uuid.uuid4().hex[:12]}{ext}"
    (upload_dir / filename).write_bytes(content)

    return {
        "image_path": f"/uploads/{filename}",
        "disclaimer": IMAGE_UPLOAD_DISCLAIMER,
    }


@router.post("/service-requests", status_code=status.HTTP_201_CREATED)
def create_service_request(
    payload: ServiceRequestCreate,
    current_user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db),
):
    """Create a persisted service request with AI issue classification, price estimate, and matched electricians."""
    classifier = get_issue_classifier()
    pricer = get_price_estimator()

    clf = classifier.predict(payload.description, urgency=payload.urgency)
    chosen_category = payload.selected_category or clf["predicted_category"]
    if chosen_category not in CATEGORY_BY_NAME:
        chosen_category = clf["predicted_category"]

    loc_info = LOCALITY_MAP.get(payload.locality, LOCALITY_MAP["Connaught Place"])
    lat = payload.latitude if payload.latitude is not None else loc_info["latitude"]
    lon = payload.longitude if payload.longitude is not None else loc_info["longitude"]
    zone = loc_info["zone"]
    complexity = payload.repair_complexity or clf["suggested_complexity"]
    duration = int(CATEGORY_BY_NAME[chosen_category]["estimated_duration_mins"])

    price = pricer.estimate_price(
        service_category=chosen_category,
        repair_complexity=complexity,
        location_zone=zone,
        urgency=payload.urgency,
        time_of_service=payload.time_of_service,
        estimated_duration=duration,
    )

    hazard = clf["hazard_assessment"]
    sr = ServiceRequest(
        customer_id=current_user.id,
        description=payload.description.strip(),
        selected_category=chosen_category,
        ai_predicted_category=clf["predicted_category"],
        ai_confidence=clf["confidence_score"],
        ai_suggested_service_type=clf["suggested_service_type"],
        urgency=payload.urgency,
        repair_complexity=complexity,
        address=payload.address.strip(),
        locality=payload.locality,
        zone=zone,
        latitude=lat,
        longitude=lon,
        image_path=payload.image_path,
        hazard_detected=bool(hazard["hazard_detected"]),
        hazard_warnings=hazard["safety_instructions"] if hazard["hazard_detected"] else [],
        ai_base_price_inr=float(price["predicted_base_price_inr"]),
        ai_price_lower_inr=float(price["lower_estimate_inr"]),
        ai_price_upper_inr=float(price["upper_estimate_inr"]),
        status="open",
    )
    db.add(sr)
    db.commit()
    db.refresh(sr)

    # Run Matching Engine
    profiles = load_active_electrician_profiles(db)
    stats_map = compute_electrician_metrics_map(db)
    candidates = [
        build_electrician_reliability_and_candidate(p, stats_map)[1] for p in profiles
    ]
    matching = rank_electricians(
        candidates=candidates,
        customer_lat=lat,
        customer_lon=lon,
        target_category=chosen_category,
        urgency=payload.urgency,
        top_k=5,
    )

    return {
        "service_request": {
            "id": sr.id,
            "description": sr.description,
            "selected_category": sr.selected_category,
            "ai_predicted_category": sr.ai_predicted_category,
            "ai_confidence": sr.ai_confidence,
            "ai_suggested_service_type": sr.ai_suggested_service_type,
            "urgency": sr.urgency,
            "repair_complexity": sr.repair_complexity,
            "address": sr.address,
            "locality": sr.locality,
            "zone": sr.zone,
            "latitude": sr.latitude,
            "longitude": sr.longitude,
            "image_path": sr.image_path,
            "hazard_detected": sr.hazard_detected,
            "hazard_warnings": sr.hazard_warnings,
            "ai_base_price_inr": sr.ai_base_price_inr,
            "ai_price_lower_inr": sr.ai_price_lower_inr,
            "ai_price_upper_inr": sr.ai_price_upper_inr,
            "created_at": sr.created_at.isoformat(),
        },
        "classification": clf,
        "price_estimate": price,
        "matching": matching,
    }


@router.get("/service-requests")
def list_my_service_requests(
    current_user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db),
):
    """List service requests created by the authenticated customer."""
    reqs = (
        db.query(ServiceRequest)
        .filter(ServiceRequest.customer_id == current_user.id)
        .order_by(ServiceRequest.created_at.desc())
        .all()
    )
    return {
        "service_requests": [
            {
                "id": sr.id,
                "description": sr.description,
                "selected_category": sr.selected_category,
                "ai_predicted_category": sr.ai_predicted_category,
                "ai_confidence": sr.ai_confidence,
                "urgency": sr.urgency,
                "locality": sr.locality,
                "ai_base_price_inr": sr.ai_base_price_inr,
                "ai_price_lower_inr": sr.ai_price_lower_inr,
                "ai_price_upper_inr": sr.ai_price_upper_inr,
                "hazard_detected": sr.hazard_detected,
                "status": sr.status,
                "created_at": sr.created_at.isoformat(),
            }
            for sr in reqs
        ]
    }


@router.post("/bookings", status_code=status.HTTP_201_CREATED)
def create_booking(
    payload: BookingCreate,
    current_user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db),
):
    """Request a booking with a selected electrician for an existing ServiceRequest."""
    sr = (
        db.query(ServiceRequest)
        .filter(
            ServiceRequest.id == payload.service_request_id,
            ServiceRequest.customer_id == current_user.id,
        )
        .first()
    )
    if not sr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found.")

    elec = (
        db.query(ElectricianProfile)
        .options(joinedload(ElectricianProfile.user))
        .filter(ElectricianProfile.id == payload.electrician_id)
        .first()
    )
    if not elec or not elec.user or not elec.user.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Electrician not found.")

    if not elec.is_available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected electrician is currently marked unavailable. Please select an available electrician.",
        )

    # Compute match snapshot cleanly for auditability
    profiles = [elec]
    stats_map = compute_electrician_metrics_map(db)
    _rel, cand, _cnt = build_electrician_reliability_and_candidate(elec, stats_map)
    ranked = rank_electricians(
        candidates=[cand],
        customer_lat=sr.latitude,
        customer_lon=sr.longitude,
        target_category=sr.selected_category,
        urgency=sr.urgency,
        top_k=1,
    )
    top = ranked["recommendations"][0]
    dist_km = haversine_distance_km(sr.latitude, sr.longitude, elec.latitude, elec.longitude)
    eta = estimate_arrival_minutes(dist_km, urgency=sr.urgency)

    booking = Booking(
        service_request_id=sr.id,
        customer_id=current_user.id,
        electrician_id=elec.id,
        status="pending",
        ai_estimate_snapshot_inr=sr.ai_base_price_inr,
        estimated_arrival_mins=eta,
        match_score=top["match_score"],
        match_explanation={
            "summary": top["explanation_summary"],
            "reasons": top["explanation_reasons"],
            "distance_km": dist_km,
        },
        scheduled_slot=payload.scheduled_slot,
        time_slot_bucket=payload.time_slot_bucket,
        customer_notes=payload.customer_notes,
    )
    sr.status = "booked"
    db.add(booking)
    db.flush()

    create_notification(
        db,
        user_id=elec.user_id,
        title="New Booking Request",
        message=f"{current_user.full_name} in {sr.locality} requested {sr.selected_category} ({sr.urgency.upper()}).",
        notif_type="booking_request",
        related_booking_id=booking.id,
    )
    create_notification(
        db,
        user_id=current_user.id,
        title="Booking Request Sent",
        message=f"Sent to {elec.user.full_name} (ETA ~{eta} mins). Awaiting acceptance & quotation.",
        notif_type="booking_update",
        related_booking_id=booking.id,
    )

    db.commit()

    loaded = (
        db.query(Booking)
        .options(
            joinedload(Booking.service_request),
            joinedload(Booking.customer),
            joinedload(Booking.electrician).joinedload(ElectricianProfile.user),
            joinedload(Booking.review),
            joinedload(Booking.payment),
        )
        .filter(Booking.id == booking.id)
        .first()
    )
    return {"booking": serialize_booking(loaded)}


@router.get("/bookings")
def list_customer_bookings(
    current_user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db),
):
    """List all bookings for the authenticated customer."""
    bookings = (
        db.query(Booking)
        .options(
            joinedload(Booking.service_request),
            joinedload(Booking.customer),
            joinedload(Booking.electrician).joinedload(ElectricianProfile.user),
            joinedload(Booking.review),
            joinedload(Booking.payment),
        )
        .filter(Booking.customer_id == current_user.id)
        .order_by(Booking.created_at.desc())
        .all()
    )
    return {"bookings": [serialize_booking(b) for b in bookings]}


@router.post("/bookings/{booking_id}/review", status_code=status.HTTP_201_CREATED)
def submit_booking_review(
    booking_id: int,
    payload: ReviewCreateRequest,
    current_user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db),
):
    """Submit a rating and review for a completed booking."""
    booking = (
        db.query(Booking)
        .options(joinedload(Booking.electrician), joinedload(Booking.review))
        .filter(Booking.id == booking_id, Booking.customer_id == current_user.id)
        .first()
    )
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found.")
    if booking.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reviews can only be submitted after the job is marked completed.",
        )
    if booking.review is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A review has already been submitted for this booking.",
        )

    review = Review(
        booking_id=booking.id,
        customer_id=current_user.id,
        electrician_id=booking.electrician_id,
        rating=payload.rating,
        comment=payload.comment.strip(),
        was_on_time=payload.was_on_time,
    )
    booking.on_time_completed = payload.was_on_time
    db.add(review)

    create_notification(
        db,
        user_id=booking.electrician.user_id,
        title=f"New {payload.rating}★ Customer Review",
        message=f"{current_user.full_name} rated your job #{booking.id} {payload.rating}/5.",
        notif_type="review",
        related_booking_id=booking.id,
    )

    db.commit()
    db.refresh(review)
    return {
        "review": {
            "id": review.id,
            "booking_id": review.booking_id,
            "rating": review.rating,
            "comment": review.comment,
            "was_on_time": review.was_on_time,
            "created_at": review.created_at.isoformat(),
        }
    }
