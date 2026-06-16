from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class RecruiterNoteCreate(BaseModel):
    """Schema for adding a new recruiter note."""
    note: str = Field(..., min_length=1)

class RecruiterNoteUpdate(BaseModel):
    """Schema for editing an existing recruiter note."""
    note: str = Field(..., min_length=1)

class RecruiterNoteResponse(BaseModel):
    """Public representation of a recruiter note."""
    id: UUID
    application_id: UUID
    author_id: UUID
    note: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
