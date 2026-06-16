"""
Job request and response schemas.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator

from app.core.enums import JobStatus


# ---------------------------------------------------------------------------
# Base schemas
# ---------------------------------------------------------------------------

class JobBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=150, description="Job title")
    department: str = Field(..., min_length=2, max_length=100, description="Department name")
    location: Optional[str] = Field(None, max_length=150, description="Job location")
    employment_type: Optional[str] = Field(None, max_length=50, description="e.g., Full-time, Contract")
    experience_required: Optional[str] = Field(None, max_length=100, description="e.g., 3-5 years")
    description: str = Field(..., min_length=10, description="Detailed job description")
    requirements: str = Field(..., min_length=10, description="Job requirements")
    responsibilities: Optional[str] = Field(None, description="Key responsibilities")
    salary_range: Optional[str] = Field(None, max_length=100, description="e.g., $100k - $120k")

    @field_validator("description", "requirements")
    @classmethod
    def validate_not_empty_text(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field cannot be empty.")
        return v.strip()


class JobCreate(JobBase):
    """Payload for POST /jobs"""
    pass


class JobUpdate(BaseModel):
    """Payload for PATCH /jobs/{id}"""
    title: Optional[str] = Field(None, min_length=2, max_length=150)
    department: Optional[str] = Field(None, min_length=2, max_length=100)
    location: Optional[str] = Field(None, max_length=150)
    employment_type: Optional[str] = Field(None, max_length=50)
    experience_required: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, min_length=10)
    requirements: Optional[str] = Field(None, min_length=10)
    responsibilities: Optional[str] = Field(None)
    salary_range: Optional[str] = Field(None, max_length=100)

    @field_validator("description", "requirements")
    @classmethod
    def validate_not_empty_text(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v.strip():
                raise ValueError("Field cannot be empty.")
            return v.strip()
        return v

    def to_update_dict(self) -> dict:
        """Return only explicitly set fields."""
        return self.model_dump(exclude_unset=True, exclude_none=True)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class JobResponse(JobBase):
    """Safe representation of a Job."""
    id: str
    status: JobStatus
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
