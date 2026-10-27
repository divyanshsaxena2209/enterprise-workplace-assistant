"""
Authentication router — existing Supabase routes plus the staged Cognito identity-link route.

Legacy signup/login/logout continue to use AuthService and Supabase Auth.
Errors are handled centrally by the error middleware — no try/except here.
"""

import logging
import secrets

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials

from app.core.security import bearer_scheme
from app.core.config import settings
from app.core.cognito_security import decode_cognito_id_token
from app.core.enums import UserRole
from app.core.exceptions import AuthenticationError, AuthorizationError, ConflictError, DatabaseError, NotFoundError
from app.repositories.cognito_identity_repository import CognitoIdentityRepository
from app.repositories.management_access_request_repository import ManagementAccessRequestRepository
from app.repositories.profile_repository import ProfileRepository
from app.db.supabase import create_supabase_auth_client, get_supabase_client
from app.dependencies.auth import get_current_user
from app.schemas.auth import CognitoLinkRequest, LoginRequest, SignupRequest, TokenResponse
from app.schemas.common import ErrorResponse, SuccessResponse
from app.schemas.profile import ProfileResponse
from app.services.auth_service import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

logger = logging.getLogger(__name__)

def _find_supabase_auth_user_by_email(auth_client, email: str):
    """Find an existing Supabase Auth identity by exact normalized email."""
    response = auth_client.auth.admin.list_users(page=1, per_page=1000)
    if isinstance(response, list):
        users = response
    elif isinstance(response, dict):
        users = response.get("users") or (response.get("data") or {}).get("users") or []
    else:
        users = getattr(response, "users", None)
        if users is None:
            data = getattr(response, "data", None)
            users = getattr(data, "users", None) if data is not None else None
    normalized_email = email.strip().lower()
    for user in users or []:
        if isinstance(user, dict):
            user_email = user.get("email")
        else:
            user_email = getattr(user, "email", None)
        if isinstance(user_email, str) and user_email.strip().lower() == normalized_email:
            return user
    return None


def _auth_user_id(user):
    return user.get("id") if isinstance(user, dict) else getattr(user, "id", None)



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
    """Link a Cognito identity only after matching verified email to the Auth user record."""
    claims = decode_cognito_id_token(body.id_token, body.nonce)
    cognito_email = str(claims["email"]).strip().lower()

    client = get_supabase_client()
    auth_client = create_supabase_auth_client()
    profile_repo = ProfileRepository(client)
    profile = profile_repo.get_by_email(cognito_email)
    if profile is None:
        # A deleted public profile can leave the corresponding Supabase Auth
        # identity behind. Recover that identity first, including for sign-in
        # callbacks where the browser does not resend signup form fields.
        existing_auth_user = None
        try:
            existing_auth_user = _find_supabase_auth_user_by_email(auth_client, cognito_email)
        except Exception as lookup_exc:
            logger.warning(
                "Existing Supabase Auth lookup failed (exception_type=%s)",
                type(lookup_exc).__name__,
            )

        signup = body.profile
        if signup is None and existing_auth_user is None:
            raise NotFoundError(
                "No matching employee profile or Supabase Auth identity was found. Use Create an account to finish signup."
            )

        if signup is not None:
            full_name = signup.full_name
            department = signup.department
            job_title = signup.job_title
            phone = signup.phone
            location = signup.location
            bio = signup.bio
            avatar_url = signup.avatar_url
        else:
            auth_metadata = (
                existing_auth_user.get("user_metadata", {})
                if isinstance(existing_auth_user, dict)
                else getattr(existing_auth_user, "user_metadata", {})
            ) or {}
            full_name = auth_metadata.get("full_name") or cognito_email.split("@", 1)[0]
            department = auth_metadata.get("department")
            job_title = auth_metadata.get("job_title")
            phone = auth_metadata.get("phone")
            location = auth_metadata.get("location")
            bio = auth_metadata.get("bio")
            avatar_url = auth_metadata.get("avatar_url")

        # Never restore elevated application permissions from browser/user
        # metadata alone; a recreated profile defaults to EMPLOYEE and must be
        # promoted through the trusted Management authorization flow.
        profile_data_base = {
            "email": cognito_email,
            "full_name": full_name,
            "role": UserRole.EMPLOYEE.value,
            "department": department,
            "job_title": job_title,
            "phone": phone,
            "location": location,
            "bio": bio,
            "avatar_url": avatar_url,
            "is_active": True,
            "is_management_verified": False,
        }

        if existing_auth_user is not None:
            existing_user_id = _auth_user_id(existing_auth_user)
            if not existing_user_id:
                raise DatabaseError("Supabase Auth returned an existing user without an ID.")
            try:
                profile = profile_repo.upsert({
                    **profile_data_base,
                    "id": str(existing_user_id),
                })
            except Exception as exc:
                raise DatabaseError(
                    "An existing Supabase Auth identity was found, but its employee profile could not be restored."
                ) from exc
        else:
            metadata = {
                "full_name": full_name,
                "role": UserRole.EMPLOYEE.value,
                "department": department,
                "job_title": job_title,
                "phone": phone,
                "location": location,
                "bio": bio,
                "avatar_url": avatar_url,
                "is_management_verified": False,
            }
            try:
                created = auth_client.auth.admin.create_user({
                    "email": cognito_email,
                    "password": secrets.token_urlsafe(48),
                    "email_confirm": True,
                    "user_metadata": metadata,
                })
                created_user = getattr(created, "user", None) or created
            except Exception as exc:
                upstream_status = getattr(exc, "status_code", None)
                if not isinstance(upstream_status, int):
                    upstream_status = getattr(exc, "status", None)
                logger.warning(
                    "Cognito staging shadow-user provisioning failed "
                    "(exception_type=%s upstream_status=%s)",
                    type(exc).__name__,
                    upstream_status if isinstance(upstream_status, int) else None,
                )
                # A concurrent/prior signup may have created the same Auth user.
                try:
                    existing_auth_user = _find_supabase_auth_user_by_email(auth_client, cognito_email)
                except Exception as lookup_exc:
                    logger.warning(
                        "Auth identity recovery lookup failed (exception_type=%s)",
                        type(lookup_exc).__name__,
                    )
                    existing_auth_user = None
                if existing_auth_user is not None:
                    created_user = existing_auth_user
                else:
                    profile = profile_repo.get_by_email(cognito_email)
                    if profile is None:
                        raise DatabaseError(
                            "Could not provision the employee profile in the staging database. "
                            "Check staging Supabase Auth and profile-trigger configuration."
                        ) from exc

            if profile is None:
                created_user_id = _auth_user_id(created_user)
                if not created_user_id:
                    raise DatabaseError("Supabase did not return the ID for the staging Auth user.")
                try:
                    profile = profile_repo.upsert({
                        **profile_data_base,
                        "id": str(created_user_id),
                    })
                except Exception as exc:
                    raise DatabaseError(
                        "The Cognito account exists, but its employee profile could not be saved."
                    ) from exc

    # The profiles table email is application data. Cross-check it against
    # the actual Supabase Auth identity so an editable/stale profile email can
    # never be used to attach Cognito to a different account.
    try:
        auth_record = auth_client.auth.admin.get_user_by_id(str(profile.id))
        auth_user = getattr(auth_record, "user", None) or auth_record
        auth_email = getattr(auth_user, "email", None)
    except Exception as exc:
        raise AuthorizationError(
            "Could not verify the existing account's identity safely. Contact support."
        ) from exc

    if not isinstance(auth_email, str) or auth_email.strip().lower() != cognito_email:
        raise AuthorizationError(
            "The verified Cognito email does not match the linked Supabase Auth account."
        )

    if not profile.is_active:
        raise AuthenticationError("Inactive profiles cannot be linked to Cognito.")

    mapping_repo = CognitoIdentityRepository(client)
    mapping_repo.link_verified_identity(str(claims["sub"]), str(profile.id), str(claims.get("cognito:username") or claims.get("username") or "") or None)

    # Only apply the staging demo selector when a create-account flow explicitly
    # provided an access-level choice. A normal sign-in must preserve the role
    # already assigned to the profile rather than defaulting back to EMPLOYEE.
    requested_access_level = (
        body.requested_access_level
        or (body.profile.requested_access_level if body.profile is not None else None)
    )
    requested_management = requested_access_level == UserRole.MANAGEMENT.value
    allowlisted_management_email = (
        cognito_email in settings.cognito_management_email_allowlist
    )

    # Demo shortcut: deliberately limited to an explicitly enabled staging Cognito
    # deployment. Never use this self-service selector in production; the UI value
    # is user-controlled and must not be authoritative outside this isolated demo.
    if settings.cognito_demo_role_selection_enabled and requested_access_level is not None:
        desired_role = UserRole(requested_access_level)
        desired_management_verified = desired_role == UserRole.MANAGEMENT
        current_role = profile.role.value if hasattr(profile.role, "value") else str(profile.role)
        current_management_verified = bool(getattr(profile, "is_management_verified", False))
        if current_role != desired_role.value or current_management_verified != desired_management_verified:
            profile_repo.update(
                str(profile.id),
                {
                    "role": desired_role.value,
                    "is_management_verified": desired_management_verified,
                },
            )
        logger.warning(
            "Staging demo role selector applied application access level=%s",
            desired_role.value,
        )
        return SuccessResponse(
            message=(
                f"Cognito identity linked. Staging demo role selection applied: {desired_role.value}. "
                "This self-service role switch is for demonstration only."
            )
        )

    # A verified email on a trusted server-side allowlist can receive Management
    # application permissions immediately. Browser selection alone is never enough
    # unless the explicitly staging-only demo switch above is enabled.
    if requested_management and allowlisted_management_email:
        if profile.role != UserRole.MANAGEMENT or not profile.is_management_verified:
            profile = profile_repo.update(
                str(profile.id),
                {"role": UserRole.MANAGEMENT.value, "is_management_verified": True},
            )
        try:
            ManagementAccessRequestRepository(client).mark_allowlisted_approved(str(profile.id))
        except Exception as exc:
            logger.warning(
                "Trusted Management allowlist audit update failed (exception_type=%s)",
                type(exc).__name__,
            )
        return SuccessResponse(
            message="Cognito identity linked. Management access was assigned by trusted administrator configuration."
        )

    # Non-allowlisted Management selection submits a request, but never elevates role.
    if requested_management and profile.role != UserRole.MANAGEMENT:
        ManagementAccessRequestRepository(client).submit(str(profile.id))
        return SuccessResponse(
            message=(
                "Cognito account linked. Employee access is active; your Management "
                "access request is pending administrator approval."
            )
        )

    return SuccessResponse(message="Cognito identity linked to the existing profile.")
