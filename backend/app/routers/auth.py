"""
Authentication router — POST /auth/signup, /auth/login, /auth/logout, GET /auth/me

All routes use AuthService which delegates to Supabase Auth.
Errors are handled centrally by the error middleware — no try/except here.
"""

import secrets

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials

from app.core.security import bearer_scheme
from app.core.cognito_security import decode_cognito_id_token
from app.core.enums import UserRole
from app.core.exceptions import AuthenticationError, ConflictError, DatabaseError, NotFoundError
from app.repositories.cognito_identity_repository import CognitoIdentityRepository
from app.repositories.profile_repository import ProfileRepository
from app.db.supabase import get_supabase_client
from app.dependencies.auth import get_current_user
from app.schemas.auth import CognitoLinkRequest, LoginRequest, SignupRequest, TokenResponse
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


@router.post(
    "/cognito/link",
    response_model=SuccessResponse,
    summary="Link a verified Cognito identity to an existing profile",
    description=(
        "Staging migration endpoint. Verifies the Cognito ID token, OAuth nonce, "
        "and verified email, then links it to an existing Supabase profile with "
        "the same email. Application roles continue to come from the database."
    ),
)
def link_cognito_identity(body: CognitoLinkRequest) -> SuccessResponse:
    """Link a verified Cognito identity to an existing profile by verified email."""
    claims = decode_cognito_id_token(body.id_token, body.nonce)
    cognito_email = str(claims["email"]).strip().lower()

    client = get_supabase_client()
    profile_repo = ProfileRepository(client)
    profile = profile_repo.get_by_email(cognito_email)
    if profile is None:
        if body.profile is None:
            raise NotFoundError(
                "No existing profile matches this verified email. Use the signup form to provide employee profile details."
            )

        # Create a Supabase Auth shadow identity so the existing profiles.id
        # foreign key remains valid. Cognito remains the only interactive login
        # provider in Cognito mode; this random password is never returned.
        signup = body.profile
        metadata = {
            "full_name": signup.full_name,
            "role": UserRole.EMPLOYEE.value,
            "department": signup.department,
            "job_title": signup.job_title,
            "phone": signup.phone,
            "location": signup.location,
            "bio": signup.bio,
            "avatar_url": signup.avatar_url,
            "is_management_verified": False,
        }
        try:
            created = client.auth.admin.create_user({
                "email": cognito_email,
                "password": secrets.token_urlsafe(48),
                "email_confirm": True,
                "user_metadata": metadata,
            })
        except Exception as exc:
            # A concurrent request may have created the profile after the first
            # lookup. Reuse only that exact email-matched profile; never overwrite
            # an existing user's role or profile fields.
            profile = profile_repo.get_by_email(cognito_email)
            if profile is None:
                raise ConflictError(
                    "Could not provision an employee profile for this Cognito account. Please contact support."
                ) from exc

        if profile is None:
            created_user = getattr(created, "user", None) or created
            created_user_id = getattr(created_user, "id", None)
            if not created_user_id:
                raise DatabaseError("Supabase did not return the ID for the Cognito shadow user.")

            try:
                profile = profile_repo.upsert({
                    "id": str(created_user_id),
                    "email": cognito_email,
                    "full_name": signup.full_name,
                    "role": UserRole.EMPLOYEE.value,
                    "department": signup.department,
                    "job_title": signup.job_title,
                    "phone": signup.phone,
                    "location": signup.location,
                    "bio": signup.bio,
                    "avatar_url": signup.avatar_url,
                    "is_active": True,
                    "is_management_verified": False,
                })
            except Exception as exc:
                raise DatabaseError(
                    "The Cognito account was created but its employee profile could not be saved."
                ) from exc

    if not profile.is_active:
        raise AuthenticationError("Inactive profiles cannot be linked to Cognito.")

    mapping_repo = CognitoIdentityRepository(client)
    mapping_repo.create_mapping(str(claims["sub"]), str(profile.id))
    return SuccessResponse(message="Cognito identity linked to the existing profile.")
