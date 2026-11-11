"""Customer & electrician profile update schemas."""

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.core.constants import normalize_indian_phone


class CustomerProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    phone: Optional[str] = Field(default=None, min_length=10, max_length=20)
    address: Optional[str] = Field(default=None, max_length=300)
    locality: Optional[str] = Field(default=None, max_length=100)
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return normalize_indian_phone(value)


class AvailabilitySlotInput(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6)
    start_time: str = Field(default="08:00", pattern=r"^\d{2}:\d{2}$")
    end_time: str = Field(default="21:00", pattern=r"^\d{2}:\d{2}$")
    is_active: bool = True


class ElectricianProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    phone: Optional[str] = Field(default=None, min_length=10, max_length=20)
    bio: Optional[str] = Field(default=None, max_length=800)
    experience_years: Optional[int] = Field(default=None, ge=0, le=55)
    service_radius_km: Optional[float] = Field(default=None, ge=1.0, le=35.0)
    locality: Optional[str] = Field(default=None, max_length=100)
    address: Optional[str] = Field(default=None, max_length=300)
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    is_available: Optional[bool] = None
    working_hours_start: Optional[str] = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    working_hours_end: Optional[str] = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    base_visit_fee_inr: Optional[int] = Field(default=None, ge=50, le=2000)
    credential_id: Optional[str] = Field(default=None, max_length=100)
    skills: Optional[List[str]] = None
    availability_slots: Optional[List[AvailabilitySlotInput]] = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return normalize_indian_phone(value)
