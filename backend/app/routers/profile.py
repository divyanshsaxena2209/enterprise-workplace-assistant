"""
Profile router — GET /profile, PATCH /profile

Both routes require authentication. PATCH supports partial updates.
Errors are handled centrally by the error middleware.
"""

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from app.core.enums import UserRole
from app.core.exceptions import AuthorizationError, NotFoundError
from app.db.supabase import get_supabase_client
from app.dependencies.auth import get_current_user, require_management
from app.repositories.profile_repository import ProfileRepository
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


class EmployeeIdUpdateRequest(BaseModel):
    """Manager-only assignment of the generated employee identifier."""
    employee_id: str = Field(
        ...,
        pattern=r"^SS-\d{5}$",
        description="Company employee identifier in SS-12345 format.",
    )


@router.patch(
    "/employees/{profile_id}/employee-id",
    response_model=ProfileResponse,
    summary="Assign an employee identifier",
    description="Management-only update of an existing employee profile's company identifier.",
    responses={
        200: {"description": "Employee identifier assigned."},
        401: {"description": "Not authenticated."},
        403: {"description": "Management access required."},
        404: {"description": "Employee profile not found."},
        422: {"description": "Invalid employee identifier."},
    },
)
def assign_employee_id(
    profile_id: str,
    body: EmployeeIdUpdateRequest,
    _current_user: ProfileResponse = Depends(require_management),
) -> ProfileResponse:
    """Assign an employee ID only after a database-backed management role check."""
    repository = ProfileRepository(get_supabase_client())
    target = repository.get_by_id(profile_id)
    if target is None:
        raise NotFoundError("Employee profile was not found.")
    if target.role != UserRole.EMPLOYEE:
        raise AuthorizationError("Employee IDs can only be assigned to employee profiles.")
    updated = repository.update(profile_id, {"employee_id": body.employee_id})
    return ProfileResponse.from_model(updated)







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
