from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class StatusTransitionRequest(BaseModel):
    """Schema for moving an application through the hiring pipeline."""
    status: str = Field(description="The new application status")
    notes: Optional[str] = Field(None, description="Optional note for the status change")

class ApplicationStatusHistoryResponse(BaseModel):
    """Public representation of an application's status change history."""
    id: UUID
    application_id: UUID
    old_status: Optional[str]
    new_status: str
    changed_by: Optional[UUID]
    notes: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PipelineDashboardResponse(BaseModel):
    """Grouped counts of applications in each pipeline stage."""
    applied: int = 0
    under_review: int = 0
    shortlisted: int = 0
    interview_scheduled: int = 0
    interview_completed: int = 0
    offer_extended: int = 0
    hired: int = 0
    rejected: int = 0
