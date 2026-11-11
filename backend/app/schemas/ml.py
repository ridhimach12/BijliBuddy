"""AI/ML request schemas for issue classification, pricing, and electrician matching."""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class IssueAnalyzeRequest(BaseModel):
    description: str = Field(..., min_length=5, max_length=2000)
    urgency: Literal["normal", "urgent", "emergency"] = "normal"
    locality: str = Field(default="Saket", max_length=100)
    zone: Optional[str] = Field(default=None, max_length=80)
    time_of_service: Literal["morning", "afternoon", "evening", "night"] = "morning"
    repair_complexity: Optional[Literal["low", "medium", "high"]] = None


class PriceEstimateRequest(BaseModel):
    service_category: str = Field(..., min_length=2, max_length=100)
    repair_complexity: Literal["low", "medium", "high"] = "medium"
    location_zone: str = Field(default="South Delhi", max_length=80)
    urgency: Literal["normal", "urgent", "emergency"] = "normal"
    time_of_service: Literal["morning", "afternoon", "evening", "night"] = "morning"
    estimated_duration: int = Field(default=45, ge=15, le=240)


class MatchWeightsOverride(BaseModel):
    distance: float = Field(default=0.25, ge=0.0, le=1.0)
    skill: float = Field(default=0.26, ge=0.0, le=1.0)
    rating: float = Field(default=0.16, ge=0.0, le=1.0)
    acceptance_rate: float = Field(default=0.12, ge=0.0, le=1.0)
    completion_rate: float = Field(default=0.12, ge=0.0, le=1.0)
    eta: float = Field(default=0.09, ge=0.0, le=1.0)


class MatchElectriciansRequest(BaseModel):
    service_category: str = Field(..., min_length=2, max_length=100)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    urgency: Literal["normal", "urgent", "emergency"] = "normal"
    top_k: int = Field(default=5, ge=1, le=10)
    weights: Optional[MatchWeightsOverride] = None
