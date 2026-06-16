"""
Candidate request and response schemas.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, HttpUrl

from app.schemas.resume import ResumeResponse


# ---------------------------------------------------------------------------
# Candidate Output Schemas
# ---------------------------------------------------------------------------

class CandidateResponse(BaseModel):
    """Public-safe representation of a candidate."""
    id: str
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CandidateDetailResponse(BaseModel):
    """Aggregate schema combining candidate and resume for detail views."""
    candidate: CandidateResponse
    resume: Optional[ResumeResponse] = None

    model_config = {"from_attributes": True}
