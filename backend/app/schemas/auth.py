"""Authentication and user identity schemas."""

from typing import List, Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.constants import normalize_indian_phone


class UserRegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=20)
    password: str = Field(..., min_length=6, max_length=128)
    role: Literal["customer", "electrician"] = "customer"
    locality: str = Field(default="Saket", max_length=100)
    address: str = Field(default="", max_length=300)
    # Optional electrician onboarding fields
    experience_years: int = Field(default=1, ge=0, le=50)
    service_radius_km: float = Field(default=6.0, ge=1.0, le=30.0)
    skills: List[str] = Field(default_factory=lambda: ["General electrical maintenance"])
    credential_id: Optional[str] = Field(default=None, max_length=100)
    bio: str = Field(default="", max_length=600)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return normalize_indian_phone(value)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class UserSummary(BaseModel):
    id: int
    email: str
    phone: str
    full_name: str
    role: str
    is_demo: bool
    locality: Optional[str] = None
    zone: Optional[str] = None
    verification_status: Optional[str] = None
    electrician_profile_id: Optional[int] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserSummary
