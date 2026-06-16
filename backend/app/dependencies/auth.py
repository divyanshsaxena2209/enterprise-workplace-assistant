"""
RBAC dependency functions for FastAPI route protection.

Usage in a router::

    from app.dependencies.auth import require_management, require_employee, get_current_user

    @router.get("/management-only")
    def management_endpoint(user: ProfileResponse = Depends(require_management)):
        ...

    @router.get("/any-employee")
    def employee_endpoint(user: ProfileResponse = Depends(require_employee)):
        ...

    @router.get("/any-authenticated")
    def protected(user: ProfileResponse = Depends(require_authenticated_user)):
        ...

How it works:
  1. `bearer_scheme` extracts the Bearer token from the Authorization header.
  2. `decode_jwt()` verifies signature and expiry.
  3. `extract_user_id()` pulls the `sub` claim.
  4. The profile is fetched from the DB via ProfileRepository.
  5. Role checks are applied in the role-specific dependencies.

All failures raise domain exceptions which are caught by the error middleware
and converted to standardized ErrorResponse JSON.
"""

import logging
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials

from app.core.enums import UserRole
from app.core.exceptions import AuthenticationError, AuthorizationError, NotFoundError
from app.core.security import bearer_scheme, decode_jwt, extract_user_id
from app.db.supabase import get_supabase_client
from app.repositories.profile_repository import ProfileRepository
from app.schemas.profile import ProfileResponse

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Core dependency — authenticated user
# ---------------------------------------------------------------------------


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> ProfileResponse:
    """
    Core RBAC dependency — resolves the currently authenticated user.

    Priority order:
      1. If request.state.user is already set by AuthMiddleware, use it.
      2. Otherwise decode the JWT and load from DB (direct route injection).

    Raises:
        AuthenticationError: if no valid token is present.
        NotFoundError: if the user's profile doesn't exist in the DB.
        AuthenticationError: if the account is deactivated.
    """
    # Fast path: middleware already resolved the user for this request.
    if hasattr(request.state, "user") and request.state.user is not None:
        return request.state.user

    # Slow path: resolve from token directly (e.g., when middleware is bypassed).
    if credentials is None:
        raise AuthenticationError("Authorization header is missing.")

    payload = decode_jwt(credentials.credentials)
    user_id = extract_user_id(payload)

    client = get_supabase_client()
    repo = ProfileRepository(client)

    profile = repo.get_by_id(user_id)
    if profile is None:
        raise NotFoundError("User profile not found. Please contact support.")

    if not profile.is_active:
        raise AuthenticationError(
            "This account has been deactivated. Please contact your administrator."
        )

    return ProfileResponse.from_model(profile)


# ---------------------------------------------------------------------------
# Alias — semantic clarity
# ---------------------------------------------------------------------------


def require_authenticated_user(
    current_user: ProfileResponse = Depends(get_current_user),
) -> ProfileResponse:
    """
    Alias for get_current_user — use this when you want to be explicit that
    the route requires authentication but doesn't care about the specific role.
    """
    return current_user


# ---------------------------------------------------------------------------
# Role-specific dependencies
# ---------------------------------------------------------------------------


def require_management(
    current_user: ProfileResponse = Depends(get_current_user),
) -> ProfileResponse:
    """
    Require the MANAGEMENT role.

    Usage::

        @router.post("/jobs")
        def create_job(user = Depends(require_management)):
            ...

    Raises:
        AuthorizationError: if the user's role is not MANAGEMENT.
    """
    if current_user.role not in UserRole.management_roles():
        raise AuthorizationError(
            "This action requires Management-level access."
        )
    return current_user


def require_employee(
    current_user: ProfileResponse = Depends(get_current_user),
) -> ProfileResponse:
    """
    Require the EMPLOYEE role.

    Note: If you want to allow BOTH roles, use require_authenticated_user instead.

    Raises:
        AuthorizationError: if the user's role is not EMPLOYEE.
    """
    if current_user.role not in UserRole.employee_roles():
        raise AuthorizationError(
            "This action is only available to Employee-level accounts."
        )
    return current_user


# ---------------------------------------------------------------------------
# Annotated shorthand types (optional convenience)
# ---------------------------------------------------------------------------

CurrentUser = Annotated[ProfileResponse, Depends(get_current_user)]
ManagementUser = Annotated[ProfileResponse, Depends(require_management)]
EmployeeUser = Annotated[ProfileResponse, Depends(require_employee)]
