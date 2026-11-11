"""Booking serialization and lifecycle helper functions."""

from typing import Dict

from app.db.models import Booking


def serialize_booking(b: Booking) -> Dict:
    """Serialize a Booking ORM object with linked ServiceRequest, Customer, Electrician, Review, and Payment."""
    sr = b.service_request
    cust = b.customer
    elec = b.electrician
    elec_user = elec.user if elec else None

    return {
        "id": b.id,
        "service_request_id": b.service_request_id,
        "status": b.status,
        "scheduled_slot": b.scheduled_slot,
        "time_slot_bucket": b.time_slot_bucket,
        "estimated_arrival_mins": b.estimated_arrival_mins,
        "match_score": b.match_score,
        "match_explanation": b.match_explanation,
        "ai_estimate_snapshot_inr": b.ai_estimate_snapshot_inr,
        "electrician_quote_inr": b.electrician_quote_inr,
        "final_amount_inr": b.final_amount_inr,
        "customer_notes": b.customer_notes,
        "electrician_notes": b.electrician_notes,
        "cancellation_reason": b.cancellation_reason,
        "on_time_completed": b.on_time_completed,
        "created_at": b.created_at.isoformat() if b.created_at else None,
        "accepted_at": b.accepted_at.isoformat() if b.accepted_at else None,
        "started_at": b.started_at.isoformat() if b.started_at else None,
        "completed_at": b.completed_at.isoformat() if b.completed_at else None,
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
            "hazard_warnings": sr.hazard_warnings or [],
            "ai_base_price_inr": sr.ai_base_price_inr,
            "ai_price_lower_inr": sr.ai_price_lower_inr,
            "ai_price_upper_inr": sr.ai_price_upper_inr,
        }
        if sr
        else None,
        "customer": {
            "id": cust.id,
            "full_name": cust.full_name,
            "phone": cust.phone,
            "email": cust.email,
        }
        if cust
        else None,
        "electrician": {
            "id": elec.id,
            "user_id": elec.user_id,
            "full_name": elec_user.full_name if elec_user else "Electrician",
            "phone": elec_user.phone if elec_user else "",
            "locality": elec.locality,
            "zone": elec.zone,
            "latitude": elec.latitude,
            "longitude": elec.longitude,
            "experience_years": elec.experience_years,
            "verification_status": elec.verification_status,
            "is_verified": elec.verification_status == "verified",
            "is_available": elec.is_available,
            "base_visit_fee_inr": elec.base_visit_fee_inr,
        }
        if elec
        else None,
        "review": {
            "id": b.review.id,
            "rating": b.review.rating,
            "comment": b.review.comment,
            "was_on_time": b.review.was_on_time,
            "created_at": b.review.created_at.isoformat(),
        }
        if b.review
        else None,
        "payment": {
            "id": b.payment.id,
            "amount_inr": b.payment.amount_inr,
            "payment_method": b.payment.payment_method,
            "status": b.payment.status,
            "is_sandbox": b.payment.is_sandbox,
            "transaction_ref": b.payment.transaction_ref,
            "created_at": b.payment.created_at.isoformat(),
        }
        if b.payment
        else None,
    }
