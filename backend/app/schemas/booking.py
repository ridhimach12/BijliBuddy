"""Service request, booking lifecycle, review, and sandbox payment schemas."""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class ServiceRequestCreate(BaseModel):
    description: str = Field(..., min_length=5, max_length=2000)
    selected_category: Optional[str] = Field(default=None, max_length=100)
    urgency: Literal["normal", "urgent", "emergency"] = "normal"
    repair_complexity: Optional[Literal["low", "medium", "high"]] = None
    time_of_service: Literal["morning", "afternoon", "evening", "night"] = "morning"
    address: str = Field(..., min_length=4, max_length=300)
    locality: str = Field(..., min_length=2, max_length=100)
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    image_path: Optional[str] = Field(default=None, max_length=300)


class BookingCreate(BaseModel):
    service_request_id: int
    electrician_id: int
    scheduled_slot: str = Field(default="As Soon As Possible", max_length=60)
    time_slot_bucket: str = Field(default="Morning (6AM-12PM)", max_length=40)
    customer_notes: Optional[str] = Field(default=None, max_length=1000)


class BookingAcceptRejectRequest(BaseModel):
    action: Literal["accept", "reject"]
    electrician_quote_inr: Optional[float] = Field(default=None, ge=100.0, le=50000.0)
    electrician_notes: Optional[str] = Field(default=None, max_length=1000)


class BookingStatusActionRequest(BaseModel):
    final_amount_inr: Optional[float] = Field(default=None, ge=100.0, le=50000.0)
    electrician_notes: Optional[str] = Field(default=None, max_length=1000)
    on_time_completed: Optional[bool] = True


class BookingCancelRequest(BaseModel):
    reason: str = Field(default="Schedule changed by user", max_length=300)


class ReviewCreateRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str = Field(default="", max_length=1000)
    was_on_time: bool = True


class SandboxPaymentRequest(BaseModel):
    payment_method: Literal["sandbox_upi", "sandbox_card", "cash_on_completion"] = "sandbox_upi"
