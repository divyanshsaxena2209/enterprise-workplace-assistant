from fastapi import APIRouter, Depends, Query, status
from typing import Optional
from uuid import UUID
from supabase import Client

from app.db.supabase import get_supabase_client
from app.dependencies.auth import require_management, require_authenticated_user
from app.schemas.profile import ProfileResponse
from app.schemas.candidate_score import CandidateScoreResponse, CandidateScoreListResponse
from app.services.matching_service import MatchingService

router = APIRouter(prefix="/evaluations", tags=["Evaluations"])

def get_matching_service(client: Client = Depends(get_supabase_client)) -> MatchingService:
    return MatchingService(client)

@router.post(
    "/applications/{application_id}/evaluate",
    response_model=CandidateScoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Force AI Candidate Evaluation",
    description="Forces the AI evaluation engine to re-evaluate an application against its job. Restricted to Management."
)
def force_evaluate_application(
    application_id: UUID,
    current_user: ProfileResponse = Depends(require_management),
    service: MatchingService = Depends(get_matching_service)
):
    return service.evaluate_application(application_id)

@router.get(
    "/applications/{application_id}/score",
    response_model=CandidateScoreResponse,
    summary="Get Application Score",
    description="Retrieves the AI evaluation score for a specific application. Any authenticated user can access if authorized by the app logic (handled at RLS or higher level)."
)
def get_application_score(
    application_id: UUID,
    current_user: ProfileResponse = Depends(require_authenticated_user),
    service: MatchingService = Depends(get_matching_service)
):
    # Note: RLS policy on candidate_scores restricts employee access to only their own applications' scores.
    # Therefore, we can just call the service, and DB RLS protects it automatically.
    return service.get_application_score(application_id)

@router.get(
    "/scores",
    response_model=CandidateScoreListResponse,
    summary="List all evaluations",
    description="List evaluation scores. Supports pagination, recommendation filter, and score filter. Restricted to Management."
)
def list_evaluations(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    recommendation: Optional[str] = None,
    min_score: Optional[int] = Query(None, ge=0, le=100),
    current_user: ProfileResponse = Depends(require_management),
    service: MatchingService = Depends(get_matching_service)
):
    skip = (page - 1) * limit
    items, total = service.score_repo.list_scores(
        skip=skip,
        limit=limit,
        recommendation=recommendation,
        min_score=min_score
    )
    
    return CandidateScoreListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit
    )
