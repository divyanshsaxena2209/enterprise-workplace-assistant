"""
Profile router — GET /profile, PATCH /profile

Both routes require authentication. PATCH supports partial updates.
Errors are handled centrally by the error middleware.
"""

from fastapi import APIRouter, Depends, status

from app.db.supabase import get_supabase_client
from app.dependencies.auth import get_current_user
from app.schemas.common import ErrorResponse
from app.schemas.profile import ProfileResponse, ProfileUpdateRequest
from app.services.profile_service import ProfileService

router = APIRouter(
    prefix="/profile",
    tags=["Profile"],
)


def _get_profile_service() -> ProfileService:
    """Dependency factory — creates ProfileService with a fresh Supabase client."""
    return ProfileService(get_supabase_client())


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


# Employee IDs are managed by administrators, not by self-service profile edits.
# The database trigger remains responsible for generated EMP-/MGR- IDs; this route
# supports the legacy HR-assigned SS-12345 format only.
import re
from pydantic import BaseModel, Field
from app.core.enums import UserRole
from app.core.exceptions import AuthorizationError, NotFoundError
from app.repositories.profile_repository import ProfileRepository
from app.dependencies.auth import require_management


class EmployeeIdUpdateRequest(BaseModel):
    employee_id: str = Field(
        pattern=r"^SS-[0-9]{5}$",
        description="Legacy HR-assigned employee identifier in SS-12345 format.",
    )


@router.patch(
    "/employees/{profile_id}/employee-id",
    response_model=ProfileResponse,
    summary="Assign an employee ID",
    description="Management-only assignment of a validated employee ID to an employee profile.",
)
def assign_employee_id(
    profile_id: str,
    body: EmployeeIdUpdateRequest,
    current_user: ProfileResponse = Depends(require_management),
) -> ProfileResponse:
    """Assign an HR-issued ID; never let employees edit their own ID or roles."""
    repository = ProfileRepository(get_supabase_client())
    target = repository.get_by_id(profile_id)
    if target is None:
        raise NotFoundError("The employee profile was not found.")
    if target.role != UserRole.EMPLOYEE:
        raise AuthorizationError("Employee IDs can only be assigned to employee profiles.")
    updated = repository.update(profile_id, {"employee_id": body.employee_id})
    return ProfileResponse.from_model(updated)


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
