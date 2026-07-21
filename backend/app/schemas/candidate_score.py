from pydantic import BaseModel, ConfigDict, Field
from typing import List, Literal, Optional
from datetime import datetime
from uuid import UUID

RecommendationLevel = Literal["Strongly Recommend", "Recommend", "Consider", "Reject"]

class CandidateScoreCreate(BaseModel):
    """Internal schema for creating an evaluation score in the database."""
    application_id: UUID
    match_percentage: int = Field(ge=0, le=100)
    ai_summary: str
    strengths: List[str]
    weaknesses: List[str]
    recommendation: RecommendationLevel

class CandidateScoreResponse(BaseModel):
    """Public representation of an AI candidate score."""
    id: UUID
    application_id: UUID
    match_percentage: int
    relative_score: Optional[int] = None
    ai_summary: str
    strengths: List[str]
    weaknesses: List[str]
    recommendation: RecommendationLevel
    evaluated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CandidateScoreListResponse(BaseModel):
    """Paginated list of candidate scores."""
    items: List[CandidateScoreResponse]
    total: int
    page: int
    limit: int
