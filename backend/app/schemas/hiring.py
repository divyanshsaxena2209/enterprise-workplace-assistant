from pydantic import BaseModel, Field, EmailStr
from typing import List, Dict, Any, Optional
from enum import Enum

class CandidateStatusEnum(str, Enum):
    APPLIED = "APPLIED"
    SCREENING = "SCREENING"
    SHORTLISTED = "SHORTLISTED"
    REJECTED = "REJECTED"
    HIRED = "HIRED"

# Job Schemas
class JobBase(BaseModel):
    title: str = Field(..., description="Job Title")
    department: Optional[str] = Field(None, description="Department")
    description: str = Field(..., description="Full Job Description")
    requirements: List[str] = Field(default=[], description="List of core requirements")

class JobCreate(JobBase):
    pass

class JobResponse(JobBase):
    id: str
    status: str
    created_at: str

    class Config:
        from_attributes = True

# Resume Parsing Structured Outputs
class ExperienceDetail(BaseModel):
    role: str = Field(..., description="Job title / Role name")
    company: str = Field(..., description="Company name")
    duration: str = Field(..., description="Duration, e.g., '2 years', '2020-2022'")
    description: Optional[str] = Field(None, description="Key duties and achievements")

class ResumeScreeningResult(BaseModel):
    first_name: str = Field(..., description="First Name of the candidate")
    last_name: str = Field(..., description="Last Name of the candidate")
    email: EmailStr = Field(..., description="Email address extracted from the resume")
    suitability_score: int = Field(..., description="Match score from 0 to 100 based on job requirements")
    match_explanation: str = Field(..., description="Detailed explanation of candidate strengths, weaknesses, and rationale for suitability score")
    parsed_skills: List[str] = Field(..., description="Core list of skills found in the resume")
    parsed_experience: List[ExperienceDetail] = Field(..., description="List of professional work experiences")

# Request DTOs
class ScreenResumeRequest(BaseModel):
    resume_file_path: str = Field(..., description="Path to file in Supabase storage")
    job_id: str = Field(..., description="ID of the job description to match against")

class ScreenResumeResponse(BaseModel):
    candidate_id: str
    first_name: str
    last_name: str
    email: str
    suitability_score: int
    match_explanation: str
    parsed_skills: List[str]
    parsed_experience: List[Dict[str, Any]]
    status: str
