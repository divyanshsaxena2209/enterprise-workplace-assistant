from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from app.schemas.job import JobResponse
from app.schemas.candidate import CandidateResponse
from app.schemas.resume import ResumeResponse
from app.schemas.candidate_score import CandidateScoreResponse
from app.schemas.pipeline import ApplicationStatusHistoryResponse
from app.schemas.recruiter_notes import RecruiterNoteResponse

# ---------------------------------------------------------------------------
# Application Input Schemas
# ---------------------------------------------------------------------------

class ApplicationCreate(BaseModel):
    """Schema for submitting a new application."""
    job_id: UUID
    candidate_id: UUID
    resume_id: UUID


# ---------------------------------------------------------------------------
# Application Output Schemas
# ---------------------------------------------------------------------------

class ApplicationResponse(BaseModel):
    """Standard representation of an application."""
    id: UUID
    job_id: UUID
    candidate_id: UUID
    resume_id: UUID
    user_id: Optional[UUID] = None
    status: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    candidate: Optional[CandidateResponse] = None
    score: Optional[CandidateScoreResponse] = None
    job: Optional[JobResponse] = None
    interviews: List['InterviewResponse'] = []

    model_config = ConfigDict(from_attributes=True)


class ApplicationListResponse(BaseModel):
    """Paginated list of applications."""
    items: List[ApplicationResponse]
    total: int
    page: int
    limit: int


class ApplicationDetailResponse(BaseModel):
    """Detailed representation of an application including related entities."""
    application: ApplicationResponse
    job: Optional[JobResponse] = None
    candidate: Optional[CandidateResponse] = None
    resume: Optional[ResumeResponse] = None
    score: Optional[CandidateScoreResponse] = None
    notes: List[RecruiterNoteResponse] = []
    history: List[ApplicationStatusHistoryResponse] = []
    interviews: List['InterviewResponse'] = []

    model_config = ConfigDict(from_attributes=True)

from app.schemas.interview import InterviewResponse
ApplicationDetailResponse.model_rebuild()
ApplicationResponse.model_rebuild()
