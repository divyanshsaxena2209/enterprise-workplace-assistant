"""
Candidates Router
Handles retrieving and deleting candidates.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from app.db.supabase import get_supabase_client
from app.dependencies.auth import get_current_user, require_management
from app.schemas.profile import ProfileResponse
from app.schemas.common import ErrorResponse, PaginatedResponse, SuccessResponse
from app.schemas.candidate import CandidateResponse, CandidateDetailResponse
from app.repositories.candidate_repository import CandidateRepository

router = APIRouter(
    prefix="/candidates",
    tags=["Candidates"],
)


def _get_candidate_repo() -> CandidateRepository:
    return CandidateRepository(get_supabase_client())


@router.get(
    "",
    response_model=PaginatedResponse[CandidateResponse],
    summary="List all candidates",
    description="Retrieves a paginated list of candidates. Supports optional search by name or email.",
    responses={
        200: {"description": "List of candidates.", "model": PaginatedResponse[CandidateResponse]},
        401: {"description": "Not authenticated.", "model": ErrorResponse},
    },
)
def list_candidates(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    current_user: ProfileResponse = Depends(get_current_user),
    repo: CandidateRepository = Depends(_get_candidate_repo),
) -> PaginatedResponse[CandidateResponse]:
    """
    **List active candidates.**
    """
    skip = (page - 1) * page_size
    candidates = repo.get_candidates(skip=skip, limit=page_size, search=search)
    
    return PaginatedResponse(
        data=candidates,
        page=page,
        page_size=page_size,
        # Note: Total count would require a separate count query in Supabase.
        # For simplicity, returning 0 or omitting total if not strictly needed.
    )


@router.get(
    "/{candidate_id}",
    response_model=CandidateDetailResponse,
    summary="Get candidate details",
    description="Retrieves a candidate's profile, parsed resume data, and AI score.",
    responses={
        200: {"description": "Candidate details.", "model": CandidateDetailResponse},
        401: {"description": "Not authenticated.", "model": ErrorResponse},
        404: {"description": "Candidate not found.", "model": ErrorResponse},
    },
)
def get_candidate(
    candidate_id: str,
    current_user: ProfileResponse = Depends(get_current_user),
    repo: CandidateRepository = Depends(_get_candidate_repo),
) -> CandidateDetailResponse:
    """
    **Get full candidate details.**
    Includes profile info, latest resume, and latest AI evaluation score.
    """
    return repo.get_candidate_by_id(candidate_id)


@router.delete(
    "/{candidate_id}",
    response_model=SuccessResponse,
    summary="Delete a candidate",
    description="Soft deletes a candidate. Requires MANAGEMENT role.",
    responses={
        200: {"description": "Candidate deleted.", "model": SuccessResponse},
        401: {"description": "Not authenticated.", "model": ErrorResponse},
        403: {"description": "Forbidden. Requires Management role.", "model": ErrorResponse},
        404: {"description": "Candidate not found.", "model": ErrorResponse},
    },
)
def delete_candidate(
    candidate_id: str,
    current_user: ProfileResponse = Depends(require_management),
    repo: CandidateRepository = Depends(_get_candidate_repo),
) -> SuccessResponse:
    """
    **Soft delete a candidate.**
    Only accessible by users with MANAGEMENT role.
    """
    repo.soft_delete_candidate(candidate_id)
    return SuccessResponse(message="Candidate successfully deleted.")
