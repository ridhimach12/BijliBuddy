"""SQLAlchemy ORM models for all 11 BijliBuddy tables."""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utcnow() -> datetime:
    """Return timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # customer | electrician | admin
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    customer_profile: Mapped[Optional["CustomerProfile"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    electrician_profile: Mapped[Optional["ElectricianProfile"]] = relationship(
        back_populates="user",
        uselist=False,
        foreign_keys="ElectricianProfile.user_id",
        cascade="all, delete-orphan",
    )
    service_requests: Mapped[List["ServiceRequest"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan"
    )
    customer_bookings: Mapped[List["Booking"]] = relationship(
        back_populates="customer", foreign_keys="Booking.customer_id"
    )
    notifications: Mapped[List["Notification"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class CustomerProfile(Base):
    __tablename__ = "customer_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    address: Mapped[str] = mapped_column(String(300), default="", nullable=False)
    locality: Mapped[str] = mapped_column(String(100), default="Connaught Place", nullable=False, index=True)
    zone: Mapped[str] = mapped_column(String(80), default="Central Delhi", nullable=False)
    latitude: Mapped[float] = mapped_column(Float, default=28.6315, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, default=77.2167, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    user: Mapped["User"] = relationship(back_populates="customer_profile")


class ElectricianProfile(Base):
    __tablename__ = "electrician_profiles"
    __table_args__ = (
        Index("ix_electrician_loc_avail", "locality", "is_available"),
        Index("ix_electrician_verification", "verification_status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    bio: Mapped[str] = mapped_column(Text, default="", nullable=False)
    experience_years: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    service_radius_km: Mapped[float] = mapped_column(Float, default=6.0, nullable=False)
    locality: Mapped[str] = mapped_column(String(100), default="Connaught Place", nullable=False, index=True)
    zone: Mapped[str] = mapped_column(String(80), default="Central Delhi", nullable=False)
    address: Mapped[str] = mapped_column(String(300), default="", nullable=False)
    latitude: Mapped[float] = mapped_column(Float, default=28.6315, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, default=77.2167, nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    working_hours_start: Mapped[str] = mapped_column(String(10), default="08:00", nullable=False)
    working_hours_end: Mapped[str] = mapped_column(String(10), default="21:00", nullable=False)
    # Verification must ONLY become 'verified' through explicit Admin approval
    verification_status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False
    )  # unverified | pending | verified | rejected
    credential_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    verification_notes: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    verified_by_admin_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    base_visit_fee_inr: Mapped[int] = mapped_column(Integer, default=199, nullable=False)
    total_earnings_inr: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    user: Mapped["User"] = relationship(back_populates="electrician_profile", foreign_keys=[user_id])
    verified_by_admin: Mapped[Optional["User"]] = relationship(foreign_keys=[verified_by_admin_id])
    skills: Mapped[List["ElectricianSkill"]] = relationship(
        back_populates="electrician", cascade="all, delete-orphan"
    )
    availability_slots: Mapped[List["Availability"]] = relationship(
        back_populates="electrician", cascade="all, delete-orphan"
    )
    bookings: Mapped[List["Booking"]] = relationship(back_populates="electrician")
    reviews: Mapped[List["Review"]] = relationship(back_populates="electrician")


class ServiceCategory(Base):
    __tablename__ = "service_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    base_price_inr: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_duration_mins: Mapped[int] = mapped_column(Integer, default=45, nullable=False)
    safety_level: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    icon_name: Mapped[str] = mapped_column(String(50), default="Zap", nullable=False)

    skills: Mapped[List["ElectricianSkill"]] = relationship(back_populates="category", cascade="all, delete-orphan")


class ElectricianSkill(Base):
    __tablename__ = "electrician_skills"
    __table_args__ = (
        UniqueConstraint("electrician_id", "category_id", name="uq_electrician_category_skill"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    electrician_id: Mapped[int] = mapped_column(
        ForeignKey("electrician_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("service_categories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    proficiency_level: Mapped[str] = mapped_column(String(30), default="expert", nullable=False)
    years_experience: Mapped[int] = mapped_column(Integer, default=2, nullable=False)

    electrician: Mapped["ElectricianProfile"] = relationship(back_populates="skills")
    category: Mapped["ServiceCategory"] = relationship(back_populates="skills")


class Availability(Base):
    __tablename__ = "availability"
    __table_args__ = (
        UniqueConstraint("electrician_id", "day_of_week", name="uq_electrician_day_avail"),
        CheckConstraint("day_of_week >= 0 AND day_of_week <= 6", name="ck_day_of_week_range"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    electrician_id: Mapped[int] = mapped_column(
        ForeignKey("electrician_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Mon .. 6=Sun
    start_time: Mapped[str] = mapped_column(String(10), default="08:00", nullable=False)
    end_time: Mapped[str] = mapped_column(String(10), default="21:00", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    electrician: Mapped["ElectricianProfile"] = relationship(back_populates="availability_slots")


class ServiceRequest(Base):
    __tablename__ = "service_requests"
    __table_args__ = (
        Index("ix_sr_locality_created", "locality", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    selected_category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    ai_predicted_category: Mapped[str] = mapped_column(String(100), nullable=False)
    ai_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    ai_suggested_service_type: Mapped[str] = mapped_column(String(150), nullable=False)
    urgency: Mapped[str] = mapped_column(String(20), default="normal", nullable=False)  # normal | urgent | emergency
    repair_complexity: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    address: Mapped[str] = mapped_column(String(300), nullable=False)
    locality: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    zone: Mapped[str] = mapped_column(String(80), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    image_path: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    hazard_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    hazard_warnings: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    ai_base_price_inr: Mapped[float] = mapped_column(Float, nullable=False)
    ai_price_lower_inr: Mapped[float] = mapped_column(Float, nullable=False)
    ai_price_upper_inr: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="open", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    customer: Mapped["User"] = relationship(back_populates="service_requests")
    bookings: Mapped[List["Booking"]] = relationship(back_populates="service_request", cascade="all, delete-orphan")


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        Index("ix_booking_elec_status", "electrician_id", "status"),
        Index("ix_booking_cust_status", "customer_id", "status"),
        Index("ix_booking_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    service_request_id: Mapped[int] = mapped_column(
        ForeignKey("service_requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    electrician_id: Mapped[int] = mapped_column(
        ForeignKey("electrician_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(30), default="pending", nullable=False, index=True
    )  # pending | accepted | in_progress | completed | rejected | cancelled
    ai_estimate_snapshot_inr: Mapped[float] = mapped_column(Float, nullable=False)
    electrician_quote_inr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    final_amount_inr: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    estimated_arrival_mins: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    match_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    match_explanation: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    scheduled_slot: Mapped[str] = mapped_column(String(60), default="As Soon As Possible", nullable=False)
    time_slot_bucket: Mapped[str] = mapped_column(String(40), default="Morning (6AM-12PM)", nullable=False)
    customer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    electrician_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    on_time_completed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    service_request: Mapped["ServiceRequest"] = relationship(back_populates="bookings")
    customer: Mapped["User"] = relationship(back_populates="customer_bookings", foreign_keys=[customer_id])
    electrician: Mapped["ElectricianProfile"] = relationship(back_populates="bookings")
    review: Mapped[Optional["Review"]] = relationship(
        back_populates="booking", uselist=False, cascade="all, delete-orphan"
    )
    payment: Mapped[Optional["Payment"]] = relationship(
        back_populates="booking", uselist=False, cascade="all, delete-orphan"
    )


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_review_rating_1_5"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id", ondelete="CASCADE"), unique=True, nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    electrician_id: Mapped[int] = mapped_column(
        ForeignKey("electrician_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str] = mapped_column(Text, default="", nullable=False)
    was_on_time: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    booking: Mapped["Booking"] = relationship(back_populates="review")
    electrician: Mapped["ElectricianProfile"] = relationship(back_populates="reviews")


class Payment(Base):
    """Demonstration / sandbox payment records only — no live payment gateway."""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id", ondelete="CASCADE"), unique=True, nullable=False)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount_inr: Mapped[float] = mapped_column(Float, nullable=False)
    payment_method: Mapped[str] = mapped_column(String(40), default="sandbox_upi", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)  # pending | demo_paid | refunded
    is_sandbox: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    transaction_ref: Mapped[str] = mapped_column(String(80), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    booking: Mapped["Booking"] = relationship(back_populates="payment")


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notif_user_read", "user_id", "is_read"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(40), default="booking_update", nullable=False)
    related_booking_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    user: Mapped["User"] = relationship(back_populates="notifications")
