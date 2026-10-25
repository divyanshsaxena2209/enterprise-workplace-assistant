"""
JWT verification and low-level token utilities.

Supabase-issued access tokens are signed credentials. This module verifies the
signature and expiry before a caller may use the `sub` claim to resolve a user.
Authorization logic (role checks) lives in app/dependencies/auth.py.
Database queries live in app/repositories/.
"""

import jwt
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Any

from app.core.config import settings
from app.core.exceptions import AuthenticationError

bearer_scheme = HTTPBearer(auto_error=False)


def decode_jwt(token: str) -> dict[str, Any]:
    """
    Verify a Supabase-issued JWT with the configured server-side signing secret.

    This application currently supports HS256 Supabase JWTs. If Supabase has
    been configured to use asymmetric signing keys, replace this with issuer-
    configured JWKS validation rather than disabling signature verification.
    """
    secret = settings.SUPABASE_JWT_SECRET
    if not secret:
        # Never accept an unsigned/unverified token, including in development.
        raise AuthenticationError("JWT verification is not configured on the server.")

    try:
        return jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options={"verify_signature": True, "verify_exp": True, "verify_aud": False},
        )
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationError("Token has expired. Please log in again.") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthenticationError("Invalid authentication token.") from exc


def extract_user_id(payload: dict[str, Any]) -> str:
    """Extract the user UUID (sub claim) from a verified JWT payload."""
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Token payload is missing the user identifier (sub).")
    return user_id


def verify_token(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> dict[str, Any]:
    """FastAPI security dependency that returns only a verified JWT payload."""
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
        ) from exc
