"""
JWT verification and low-level token utilities.

This module is intentionally thin — it only handles token cryptography.
Authorization logic (role checks) lives in app/dependencies/auth.py.
Database queries live in app/repositories/.
"""

import jwt
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Any

from app.core.config import settings
from app.core.exceptions import AuthenticationError

# HTTPBearer extractor used as a FastAPI Security dependency.
# auto_error=False lets the middleware handle missing tokens gracefully.
bearer_scheme = HTTPBearer(auto_error=False)


def decode_jwt(token: str) -> dict[str, Any]:
    """
    Decode and verify a Supabase-issued JWT.

    Returns the decoded payload dict on success.
    Raises AuthenticationError on any failure.
    """
    if not settings.SUPABASE_JWT_SECRET:
        # Fall back to unverified decode in development if secret not set.
        # In production this will raise because is_production guard below.
        if settings.is_production:
            raise AuthenticationError("JWT secret not configured on server.")
        try:
            return jwt.decode(
                token,
                options={"verify_signature": False, "verify_aud": False},
                algorithms=["HS256"],
            )
        except jwt.DecodeError as exc:
            raise AuthenticationError(f"Malformed JWT: {exc}") from exc

    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},  # Supabase uses 'authenticated' aud
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired. Please log in again.")
    except jwt.InvalidTokenError as exc:
        raise AuthenticationError(f"Invalid authentication token: {exc}")


def extract_user_id(payload: dict[str, Any]) -> str:
    """Extract the user UUID (sub claim) from a decoded JWT payload."""
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Token payload is missing the user identifier (sub).")
    return user_id


def verify_token(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> dict[str, Any]:
    """
    FastAPI security dependency — extracts and verifies the Bearer token.

    Usage::

        @router.get("/protected")
        def protected(payload: dict = Security(verify_token)):
            ...

    Prefer using the higher-level dependencies in app/dependencies/auth.py
    which also load the full user profile.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is missing.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return decode_jwt(credentials.credentials)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.message,
            headers={"WWW-Authenticate": "Bearer"},
        )
