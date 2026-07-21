from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

class InterviewCreate(BaseModel):
    scheduled_at: datetime
    meeting_link: Optional[str] = None
    management_notes: Optional[str] = None

class InterviewRespond(BaseModel):
    status: str # 'Accepted', 'Rejected', 'Reschedule Requested'
    candidate_notes: Optional[str] = None

class InterviewResponse(BaseModel):
    id: UUID
    application_id: UUID
    scheduled_at: datetime
    status: str
    meeting_link: Optional[str] = None
    management_notes: Optional[str] = None
    candidate_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
