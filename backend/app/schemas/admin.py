"""Admin verification and governance schemas."""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class VerificationDecisionRequest(BaseModel):
    decision: Literal["verified", "rejected", "pending"]
    verification_notes: Optional[str] = Field(default=None, max_length=300)
