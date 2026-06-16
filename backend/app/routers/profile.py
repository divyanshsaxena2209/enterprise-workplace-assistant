"""
Profile router — GET /profile, PATCH /profile

Both routes require authentication. PATCH supports partial updates.
Errors are handled centrally by the error middleware.
"""

from fastapi import APIRouter, Depends, status

from app.db.supabase import get_supabase_client
from app.dependencies.auth import get_current_user
from app.schemas.common import ErrorResponse, SuccessResponse
from app.schemas.profile import ProfileResponse, ProfileUpdateRequest
from app.services.profile_service import ProfileService

router = APIRouter(
    prefix="/profile",
    tags=["Profile"],
)


def _get_profile_service() -> ProfileService:
    """Dependency factory — creates ProfileService with a fresh Supabase client."""
    return ProfileService(get_supabase_client())


# ---------------------------------------------------------------------------
# GET /profile
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=ProfileResponse,
    summary="Get the authenticated user's profile",
    description=(
        "Returns the complete profile for the currently authenticated user. "
        "Includes all optional fields such as department, job title, phone, and bio."
    ),
    responses={
        200: {"description": "User profile.", "model": ProfileResponse},
        401: {"description": "Not authenticated.", "model": ErrorResponse},
        404: {"description": "Profile not found.", "model": ErrorResponse},
    },
)
def get_profile(
    current_user: ProfileResponse = Depends(get_current_user),
    svc: ProfileService = Depends(_get_profile_service),
) -> ProfileResponse:
    """
    **Retrieve the authenticated user's full profile.**

    Returns all fields including optional ones that may be null if not yet filled in.
    """
    return svc.get_profile(current_user.id)


# ---------------------------------------------------------------------------
# PATCH /profile
# ---------------------------------------------------------------------------


@router.patch(
    "",
    response_model=ProfileResponse,
    summary="Update the authenticated user's profile",
    description=(
        "Partially update the authenticated user's profile. "
        "Only fields included in the request body are updated. "
        "Note: email and role cannot be changed via this endpoint."
    ),
    responses={
        200: {"description": "Updated profile.", "model": ProfileResponse},
        401: {"description": "Not authenticated.", "model": ErrorResponse},
        404: {"description": "Profile not found.", "model": ErrorResponse},
        422: {"description": "Validation error.", "model": ErrorResponse},
    },
)
def update_profile(
    body: ProfileUpdateRequest,
    current_user: ProfileResponse = Depends(get_current_user),
    svc: ProfileService = Depends(_get_profile_service),
) -> ProfileResponse:
    """
    **Update the authenticated user's profile.**

    Supports partial updates — only provided fields are changed.

    Updatable fields:
    - `full_name`
    - `phone` (E.164 format, e.g. +14155552671)
    - `department`
    - `job_title`
    - `location`
    - `bio`
    - `avatar_url`
    """
    return svc.update_profile(current_user.id, body)
