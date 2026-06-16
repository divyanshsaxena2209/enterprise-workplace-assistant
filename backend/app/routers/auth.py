"""
Authentication router — POST /auth/signup, /auth/login, /auth/logout, GET /auth/me

All routes use AuthService which delegates to Supabase Auth.
Errors are handled centrally by the error middleware — no try/except here.
"""

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials

from app.core.security import bearer_scheme
from app.db.supabase import get_supabase_client
from app.dependencies.auth import get_current_user
from app.schemas.auth import LoginRequest, SignupRequest, TokenResponse
from app.schemas.common import ErrorResponse, SuccessResponse
from app.schemas.profile import ProfileResponse
from app.services.auth_service import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


def _get_auth_service() -> AuthService:
    """Dependency factory — creates AuthService with a fresh Supabase client."""
    return AuthService(get_supabase_client())


# ---------------------------------------------------------------------------
# POST /auth/signup
# ---------------------------------------------------------------------------


@router.post(
    "/signup",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description=(
        "Create a new account. On success, returns access and refresh tokens "
        "along with the user's full profile. "
        "Passwords must be at least 8 characters and contain uppercase, lowercase, and a digit."
    ),
    responses={
        201: {"description": "Account created successfully.", "model": TokenResponse},
        409: {"description": "Email already registered.", "model": ErrorResponse},
        422: {"description": "Validation error.", "model": ErrorResponse},
    },
)
def signup(
    body: SignupRequest,
    svc: AuthService = Depends(_get_auth_service),
) -> TokenResponse:
    """
    **Register a new user account.**

    - Validates email uniqueness
    - Creates Supabase Auth user
    - Creates profile record with all provided metadata
    - Returns JWT access + refresh tokens
    """
    return svc.signup(body)


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate with email and password",
    description="Log in with email and password. Returns access token, refresh token, and user profile.",
    responses={
        200: {"description": "Login successful.", "model": TokenResponse},
        401: {"description": "Invalid credentials.", "model": ErrorResponse},
        422: {"description": "Validation error.", "model": ErrorResponse},
    },
)
def login(
    body: LoginRequest,
    svc: AuthService = Depends(_get_auth_service),
) -> TokenResponse:
    """
    **Authenticate an existing user.**

    - Validates email + password against Supabase Auth
    - Checks if account is active
    - Returns access_token, refresh_token, and full profile
    """
    return svc.login(body)


# ---------------------------------------------------------------------------
# POST /auth/logout
# ---------------------------------------------------------------------------


@router.post(
    "/logout",
    response_model=SuccessResponse,
    summary="Log out the current user",
    description="Invalidate the current session. Requires a valid Bearer token.",
    responses={
        200: {"description": "Logged out successfully.", "model": SuccessResponse},
        401: {"description": "Not authenticated.", "model": ErrorResponse},
    },
)
def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    _current_user: ProfileResponse = Depends(get_current_user),
    svc: AuthService = Depends(_get_auth_service),
) -> SuccessResponse:
    """
    **Log out the authenticated user.**

    Invalidates the current session token. The client should discard
    stored tokens after calling this endpoint.
    """
    token = credentials.credentials if credentials else ""
    svc.logout(token)
    return SuccessResponse(message="Logged out successfully.")


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------


@router.get(
    "/me",
    response_model=ProfileResponse,
    summary="Get current authenticated user",
    description="Returns the full profile of the currently authenticated user.",
    responses={
        200: {"description": "Current user profile.", "model": ProfileResponse},
        401: {"description": "Not authenticated.", "model": ErrorResponse},
        404: {"description": "Profile not found.", "model": ErrorResponse},
    },
)
def get_me(
    current_user: ProfileResponse = Depends(get_current_user),
) -> ProfileResponse:
    """
    **Return the authenticated user's profile.**

    The profile includes role, department, job title, and all optional fields.
    Use this endpoint to bootstrap the frontend after login.
    """
    return current_user
