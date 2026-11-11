"""Shared booking lifecycle endpoints: detail polling, cancellation, and sandbox demo payment."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.security import get_current_user
from app.db.models import Booking, ElectricianProfile, Payment, User
from app.db.session import get_db
from app.schemas.booking import BookingCancelRequest, SandboxPaymentRequest
from app.services.booking_service import serialize_booking
from app.services.notifications import create_notification

router = APIRouter(prefix="/api/bookings", tags=["Bookings"])


def _load_authorized_booking(booking_id: int, current_user: User, db: Session) -> Booking:
    booking = (
        db.query(Booking)
        .options(
            joinedload(Booking.service_request),
            joinedload(Booking.customer),
            joinedload(Booking.electrician).joinedload(ElectricianProfile.user),
            joinedload(Booking.review),
            joinedload(Booking.payment),
        )
        .filter(Booking.id == booking_id)
        .first()
    )
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found.")

    is_owner_customer = current_user.role == "customer" and booking.customer_id == current_user.id
    is_assigned_electrician = (
        current_user.role == "electrician"
        and booking.electrician is not None
        and booking.electrician.user_id == current_user.id
    )
    if not (is_owner_customer or is_assigned_electrician or current_user.role == "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied for this booking.")
    return booking


@router.get("/{booking_id}")
def get_booking_detail(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetch full booking status and linked details (used for live status polling)."""
    booking = _load_authorized_booking(booking_id, current_user, db)
    return {"booking": serialize_booking(booking)}


@router.post("/{booking_id}/cancel")
def cancel_booking(
    booking_id: int,
    payload: BookingCancelRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel a pending or accepted booking."""
    booking = _load_authorized_booking(booking_id, current_user, db)
    if booking.status not in ("pending", "accepted"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel booking in '{booking.status}' state.",
        )

    booking.status = "cancelled"
    booking.cancellation_reason = payload.reason.strip()

    notify_user_id = (
        booking.electrician.user_id
        if current_user.id == booking.customer_id
        else booking.customer_id
    )
    create_notification(
        db,
        user_id=notify_user_id,
        title="Booking Cancelled",
        message=f"Booking #{booking.id} was cancelled ({booking.cancellation_reason}).",
        notif_type="booking_update",
        related_booking_id=booking.id,
    )
    db.commit()
    db.refresh(booking)
    return {"booking": serialize_booking(booking)}


@router.post("/{booking_id}/sandbox-payment")
def confirm_sandbox_payment(
    booking_id: int,
    payload: SandboxPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Confirm demonstration/sandbox payment on a completed booking (no real money movement)."""
    booking = _load_authorized_booking(booking_id, current_user, db)
    if current_user.role != "customer" or booking.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the booking customer can pay.")
    if booking.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment can be recorded only after job completion.",
        )

    amount = float(
        booking.final_amount_inr or booking.electrician_quote_inr or booking.ai_estimate_snapshot_inr
    )
    if booking.payment is None:
        payment = Payment(
            booking_id=booking.id,
            customer_id=current_user.id,
            amount_inr=amount,
            payment_method=payload.payment_method,
            status="demo_paid",
            is_sandbox=True,
            transaction_ref=f"DEMO-{uuid.uuid4().hex[:10].upper()}",
        )
        db.add(payment)
    else:
        booking.payment.payment_method = payload.payment_method
        booking.payment.status = "demo_paid"
        booking.payment.amount_inr = amount
        booking.payment.is_sandbox = True

    db.commit()
    db.refresh(booking)
    return {
        "notice": "Demonstration sandbox payment only — no live payment gateway transaction occurred.",
        "booking": serialize_booking(booking),
    }
