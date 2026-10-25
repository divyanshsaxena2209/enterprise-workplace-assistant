"""
RBAC dependency functions for FastAPI route protection.

A request is authorized only after its signed JWT has been validated and its
active user profile resolved from the database. Local/test bypasses must be
implemented through dependency overrides in tests, never through a magic token.
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


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> ProfileResponse:
    """
    Resolve the current authenticated user.

    Middleware may pre-populate request.state.user after verifying the same JWT.
    Otherwise, this dependency performs validation and profile lookup itself.
    """
    if getattr(request.state, "user", None) is not None:
        return request.state.user

    if credentials is None:
        raise AuthenticationError("Authorization header is missing.")

    payload = decode_jwt(credentials.credentials)
    user_id = extract_user_id(payload)

    repo = ProfileRepository(get_supabase_client())
    profile = repo.get_by_id(user_id)
    if profile is None:
        raise NotFoundError("User profile not found. Please contact support.")

    if not profile.is_active:
        raise AuthenticationError(
            "This account has been deactivated. Please contact your administrator."
        )

    return ProfileResponse.from_model(profile)


def require_authenticated_user(
    current_user: ProfileResponse = Depends(get_current_user),
) -> ProfileResponse:
    """Require a valid authenticated, active user without a role restriction."""
    return current_user


def require_management(
    current_user: ProfileResponse = Depends(get_current_user),
) -> ProfileResponse:
    """Require a management-level account."""
    if current_user.role not in UserRole.management_roles():
        raise AuthorizationError("This action requires Management-level access.")
    return current_user


def require_employee(
    current_user: ProfileResponse = Depends(get_current_user),
) -> ProfileResponse:
    """Require an employee-level account."""
    if current_user.role not in UserRole.employee_roles():
        raise AuthorizationError("This action is only available to Employee-level accounts.")
    return current_user


CurrentUser = Annotated[ProfileResponse, Depends(get_current_user)]
ManagementUser = Annotated[ProfileResponse, Depends(require_management)]
EmployeeUser = Annotated[ProfileResponse, Depends(require_employee)]
