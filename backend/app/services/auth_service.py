"""
AuthService — handles all authentication flows via Supabase Auth.

Flow for signup:
  1. Call supabase.auth.sign_up() → creates the auth.users row
  2. Supabase DB trigger (handle_new_user) creates the profile row automatically
  3. We upsert the profile to ensure all metadata fields are correct
  4. Return tokens + full ProfileResponse

Flow for login:
  1. Call supabase.auth.sign_in_with_password()
  2. Load profile from DB
  3. Return tokens + ProfileResponse

Rules:
- Raises domain exceptions from app/core/exceptions.py.
- Never raises raw HTTPException.
- No raw SQL — delegates DB work to ProfileRepository.
"""

import logging
from supabase import Client
from gotrue.errors import AuthApiError

from app.core.config import settings
from app.core.enums import UserRole
from app.core.exceptions import (
    AuthenticationError,
    BadRequestError,
    ConflictError,
    DatabaseError,
)
from app.repositories.profile_repository import ProfileRepository
from app.schemas.auth import LoginRequest, SignupRequest, TokenResponse
from app.schemas.profile import ProfileResponse

logger = logging.getLogger(__name__)


class AuthService:
    """Handles signup, login, logout, and token management via Supabase Auth."""

    def __init__(self, client: Client) -> None:
        self._db = client
        self._repo = ProfileRepository(client)

    # -------------------------------------------------------------------------
    # Signup
    # -------------------------------------------------------------------------

    def signup(self, data: SignupRequest) -> TokenResponse:
        """
        Register a new user.

        1. Check for existing email (give friendly error before Supabase rejects).
        2. Call supabase.auth.sign_up() with profile metadata.
        3. Upsert profile to guarantee all fields are stored correctly.
        4. Return access_token, refresh_token, and ProfileResponse.
        """
        # Pre-flight: check for duplicate email
        existing = self._repo.get_by_email(data.email)
        if existing:
            raise ConflictError(
                f"An account with the email '{data.email}' already exists."
            )

        # Build metadata for the DB trigger
        user_metadata = {
            "full_name": data.full_name,
            "role": data.role.value,
            "employee_id": data.employee_id,
            "department": data.department,
            "job_title": data.job_title,
            "phone": data.phone,
            "location": data.location,
            "bio": data.bio,
        }

        try:
            auth_response = self._db.auth.sign_up(
                {
                    "email": data.email,
                    "password": data.password,
                    "options": {"data": user_metadata},
                }
            )
        except AuthApiError as exc:
            logger.warning("Supabase sign_up failed: %s", exc)
            self._map_auth_error(exc)  # raises domain exception

        session = auth_response.session
        user = auth_response.user

        if not session or not user:
            raise AuthenticationError(
                "Signup succeeded but no session was returned. "
                "Check if email confirmation is required in Supabase Auth settings."
            )

        # Upsert profile — ensures all metadata is saved even if trigger fires first
        profile_data = {
            "id": user.id,
            "email": data.email.lower().strip(),
            "full_name": data.full_name,
            "role": data.role.value,
            "employee_id": data.employee_id,
            "department": data.department,
            "job_title": data.job_title,
            "phone": data.phone,
            "location": data.location,
            "bio": data.bio,
            "is_active": True,
            "is_management_verified": False,
        }

        try:
            profile_model = self._repo.upsert(profile_data)
        except Exception as exc:
            logger.error("Profile upsert failed after signup: %s", exc)
            raise DatabaseError(
                "Account created but profile setup failed. Please contact support."
            ) from exc

        return TokenResponse(
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            expires_in=session.expires_in or settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=ProfileResponse.from_model(profile_model),
        )

    # -------------------------------------------------------------------------
    # Login
    # -------------------------------------------------------------------------

    def login(self, data: LoginRequest) -> TokenResponse:
        """
        Authenticate an existing user with email + password.

        Returns tokens and the full profile on success.
        """
        try:
            auth_response = self._db.auth.sign_in_with_password(
                {"email": data.email, "password": data.password}
            )
        except AuthApiError as exc:
            logger.warning("Login failed for %s: %s", data.email, exc)
            self._map_auth_error(exc)

        session = auth_response.session
        user = auth_response.user

        if not session or not user:
            raise AuthenticationError("Login failed. Please check your credentials.")

        # Load profile from DB (authoritative source for role, is_active, etc.)
        profile_model = self._repo.get_by_id(user.id)
        if profile_model is None:
            raise AuthenticationError(
                "Account exists but profile is missing. Please contact support."
            )

        if not profile_model.is_active:
            raise AuthenticationError(
                "This account has been deactivated. Please contact your administrator."
            )

        return TokenResponse(
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            expires_in=session.expires_in or settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=ProfileResponse.from_model(profile_model),
        )

    # -------------------------------------------------------------------------
    # Logout
    # -------------------------------------------------------------------------

    def logout(self, access_token: str) -> None:
        """
        Invalidate the current session token via Supabase Admin.

        Note: Supabase uses stateless JWTs — logout only works if Supabase's
        token revocation is enabled, or for refresh token invalidation.
        """
        try:
            self._db.auth.admin.sign_out(access_token)
        except Exception as exc:
            # Logout failure is non-critical — log and continue.
            logger.warning("Logout call failed (token may already be expired): %s", exc)

    # -------------------------------------------------------------------------
    # Get current user
    # -------------------------------------------------------------------------

    def get_me(self, user_id: str) -> ProfileResponse:
        """Return the full profile of the currently authenticated user."""
        from app.services.profile_service import ProfileService

        svc = ProfileService(self._db)
        return svc.get_profile(user_id)

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _map_auth_error(exc: AuthApiError) -> None:
        """Map Supabase AuthApiError to a domain exception and raise it."""
        message = str(exc).lower()
        if "invalid login credentials" in message or "invalid email or password" in message:
            raise AuthenticationError("Invalid email or password.")
        if "user already registered" in message or "already been registered" in message:
            raise ConflictError("An account with this email already exists.")
        if "email not confirmed" in message:
            raise AuthenticationError(
                "Please confirm your email address before logging in."
            )
        if "rate limit" in message:
            raise BadRequestError("Too many requests. Please try again later.")
        # Generic fallback
        raise AuthenticationError(f"Authentication failed: {exc}")
