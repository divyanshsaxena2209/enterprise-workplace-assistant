"""
Resume request and response schemas, including structured outputs for AI parsing.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Structured output schemas (for GPT-4o)
# ---------------------------------------------------------------------------

class ParsedExperience(BaseModel):
    company: str = Field(description="Name of the company")
    role: str = Field(description="Job title or role")
    duration: str = Field(description="Duration of employment (e.g., 'Jan 2020 - Present')")
    description: str = Field(description="Summary of responsibilities and achievements")


class ParsedEducation(BaseModel):
    institution: str = Field(description="Name of the school or university")
    degree: str = Field(description="Degree obtained (e.g., 'B.S. Computer Science')")
    graduation_year: str = Field(description="Year of graduation")


class ParsedProject(BaseModel):
    name: str = Field(description="Name of the project")
    description: str = Field(description="Description of the project and technologies used")


class ParsedResumeData(BaseModel):
    """Schema for the structured JSON output from the AI resume parser."""
    full_name: str = Field(default="", description="Candidate's full name")
    email: str = Field(default="", description="Candidate's email address")
    phone: str = Field(default="", description="Candidate's phone number")
    skills: List[str] = Field(default_factory=list, description="List of technical and soft skills")
    experience: List[ParsedExperience] = Field(default_factory=list, description="Professional experience history")
    education: List[ParsedEducation] = Field(default_factory=list, description="Educational background")
    certifications: List[str] = Field(default_factory=list, description="List of certifications")
    projects: List[ParsedProject] = Field(default_factory=list, description="Notable projects")
    previous_companies: List[str] = Field(default_factory=list, description="List of previous employer names")


# ---------------------------------------------------------------------------
# API Response Schemas
# ---------------------------------------------------------------------------

class ResumeResponse(BaseModel):
    """Safe representation of a resume record."""
    id: str
    candidate_id: str
    file_name: str
    file_url: str
    parsed_json: ParsedResumeData
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class ResumeUploadResponse(BaseModel):
    """Response returned when a resume is successfully uploaded and processed."""
    candidate_id: str
    message: str = "Resume successfully uploaded and processed."
