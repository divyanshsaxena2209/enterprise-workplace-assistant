from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID

# Job Schemas
class JobBase(BaseModel):
    title: str
    department: Optional[str] = None
    description: Optional[str] = None
    requirements: List[str] = []
    experience_level: Optional[str] = None
    salary_range: Optional[str] = None
    employment_type: Optional[str] = None
    status: str = "Draft"

class JobCreate(JobBase):
    pass

class JobResponse(JobBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Candidate Schemas
class CandidateBase(BaseModel):
    name: str
    email: str
    skills: List[str] = []
    status: str = "new"

class CandidateCreate(CandidateBase):
    pass

class CandidateResponse(CandidateBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

# Resume Schemas
class ResumeBase(BaseModel):
    candidate_id: UUID
    file_url: str
    parsed_data: Optional[dict] = None
    status: str = "pending"

class ResumeCreate(ResumeBase):
    pass

class ResumeResponse(ResumeBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

# Application Schemas
class ApplicationBase(BaseModel):
    job_id: UUID
    candidate_id: UUID
    resume_id: Optional[UUID] = None
    status: str = "Applied"

class ApplicationCreate(ApplicationBase):
    pass

class ApplicationResponse(ApplicationBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Candidate Score Schemas
class CandidateScoreBase(BaseModel):
    application_id: UUID
    match_percentage: int = Field(ge=0, le=100)
    skill_overlap: List[str] = []
    ai_summary: Optional[str] = None
    strengths: List[str] = []
    weaknesses: List[str] = []
    recommendation: Optional[str] = None

class CandidateScoreCreate(CandidateScoreBase):
    pass

class CandidateScoreResponse(CandidateScoreBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
