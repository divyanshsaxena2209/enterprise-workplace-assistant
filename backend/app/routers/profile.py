"""
Profile router — GET /profile, PATCH /profile

Both routes require authentication. PATCH supports partial updates.
Errors are handled centrally by the error middleware.
"""

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field, field_validator
from typing import Literal

from app.core.enums import UserRole
from app.core.config import settings
from app.core.exceptions import AuthorizationError, NotFoundError
from app.dependencies.auth import get_current_user, require_management
from app.repositories.profile_repository import ProfileRepository
from app.repositories.management_access_request_repository import ManagementAccessRequestRepository
from app.dependencies.auth import require_management_or_employee

from app.db.supabase import get_supabase_client
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







# Employee IDs are managed by administrators, not by self-service profile edits.
# The database trigger remains responsible for generated EMP-/MGR- IDs; this route
# supports the legacy HR-assigned SS-12345 format only.
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







class DepartmentUpdateRequest(BaseModel):
    """Department assignment controlled by Management, never self-service."""

    department: str | None = Field(
        description="Authoritative employee department; null removes the assignment.",
        max_length=100,
    )
    model_config = {"extra": "forbid"}

    @field_validator("department")
    @classmethod
    def normalize_department(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Department must be non-empty; send null to remove assignment.")
        return cleaned


@router.patch(
    "/employees/{profile_id}/department",
    response_model=ProfileResponse,
    summary="Assign an employee department",
    description="Management-only change of the authoritative department used for access scoping.",
)
def assign_employee_department(
    profile_id: str,
    body: DepartmentUpdateRequest,
    current_user: ProfileResponse = Depends(require_management),
) -> ProfileResponse:
    """Only Management may change a user's department-based access scope."""
    repository = ProfileRepository(get_supabase_client())
    target = repository.get_by_id(profile_id)
    if target is None:
        raise NotFoundError("The employee profile was not found.")
    if target.role != UserRole.EMPLOYEE:
        raise AuthorizationError("Department assignment is restricted to employee profiles.")
    updated = repository.update(profile_id, {"department": body.department})
    return ProfileResponse.from_model(updated)


class ManagementAccessReviewRequest(BaseModel):
    decision: Literal["APPROVE", "REJECT"]
    reviewer_note: str | None = Field(default=None, max_length=500)
    model_config = {"extra": "forbid"}

    @field_validator("reviewer_note")
    @classmethod
    def normalize_reviewer_note(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class ManagementAccessRequestSubmit(BaseModel):
    request_note: str | None = Field(default=None, max_length=500)
    model_config = {"extra": "forbid"}

    @field_validator("request_note")
    @classmethod
    def normalize_request_note(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


@router.post(
    "/management-access-request",
    summary="Submit or resubmit a Management access request",
)
def submit_management_access_request(
    body: ManagementAccessRequestSubmit,
    current_user: ProfileResponse = Depends(require_management_or_employee),
):
    """Submitting a request never changes the caller's application role."""
    if current_user.role != UserRole.EMPLOYEE:
        raise AuthorizationError("Only Employee accounts may request Management access.")

    client = get_supabase_client()
    if str(current_user.email).strip().lower() in settings.cognito_management_email_allowlist:
        ProfileRepository(client).update(
            str(current_user.id),
            {"role": UserRole.MANAGEMENT.value, "is_management_verified": True},
        )
        request_record = ManagementAccessRequestRepository(client).mark_allowlisted_approved(
            str(current_user.id)
        )
        return {
            "request": request_record,
            "message": "Management access was assigned by the trusted administrator configuration.",
        }

    request_record = ManagementAccessRequestRepository(client).submit(
        str(current_user.id), request_note=body.request_note
    )
    return {
        "request": request_record,
        "message": (
            "Management access request submitted for administrator review."
            if request_record.get("status") == "PENDING"
            else f"Your Management access request is {request_record.get('status', 'unavailable')}."
        ),
    }


@router.get(
    "/management-access-request",
    summary="Get the authenticated user's Management access request",
)
def get_my_management_access_request(
    current_user: ProfileResponse = Depends(require_management_or_employee),
):
    """Return only the caller's own approval state; never expose the request table directly."""
    request_record = ManagementAccessRequestRepository(get_supabase_client()).get_for_profile(
        str(current_user.id)
    )
    return {"request": request_record}


@router.get(
    "/management-access-requests/pending",
    summary="List pending Management access requests",
)
def list_pending_management_access_requests(
    current_user: ProfileResponse = Depends(require_management),
):
    """Management-only inbox for requests to elevate employee application permissions."""
    client = get_supabase_client()
    request_repo = ManagementAccessRequestRepository(client)
    profile_repo = ProfileRepository(client)
    results = []
    for item in request_repo.list_pending():
        profile = profile_repo.get_by_id(str(item["profile_id"]))
        if profile is None:
            continue
        results.append({
            "profile_id": str(profile.id),
            "status": item["status"],
            "requested_role": item["requested_role"],
            "request_note": item.get("request_note"),
            "requested_at": item.get("requested_at"),
            "requester": {
                "full_name": profile.full_name,
                "email": profile.email,
                "employee_id": profile.employee_id,
                "department": profile.department,
                "job_title": profile.job_title,
                "current_role": profile.role.value if hasattr(profile.role, "value") else str(profile.role),
            },
        })
    return {"requests": results}


@router.post(
    "/management-access-requests/{profile_id}/review",
    summary="Approve or reject a Management access request",
)
def review_management_access_request(
    profile_id: str,
    body: ManagementAccessReviewRequest,
    current_user: ProfileResponse = Depends(require_management),
):
    """The DB function rechecks the reviewer's role and atomically updates role + request status."""
    request_repo = ManagementAccessRequestRepository(get_supabase_client())
    status_value = request_repo.review(
        profile_id=profile_id,
        decision=body.decision,
        reviewer_id=str(current_user.id),
        reviewer_note=body.reviewer_note,
    )
    return {
        "success": True,
        "profile_id": profile_id,
        "status": status_value,
        "message": (
            "Management access approved."
            if status_value == "APPROVED"
            else "Management access request rejected."
        ),
    }


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
    - Department is assigned by Management through the dedicated department endpoint.
    - `job_title`
    - `location`
    - `bio`
    - `avatar_url`
    """
    return svc.update_profile(current_user.id, body)
