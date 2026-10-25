"""
JWT verification and low-level token utilities.

Supabase currently issues HS256 tokens for this application. Verify the
signature and expiry before the profile's database-backed role is trusted.
The Cognito migration will replace this verifier with issuer/JWKS validation.
"""

import jwt
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Any

from app.core.config import settings
from app.core.exceptions import AuthenticationError

bearer_scheme = HTTPBearer(auto_error=False)


def decode_jwt(token: str) -> dict[str, Any]:
    """Decode a Supabase-issued JWT only after cryptographic verification."""
    secret = settings.SUPABASE_JWT_SECRET
    if not secret:
        # Failing closed is essential: unsigned tokens must never identify a user.
        raise AuthenticationError("JWT verification is not configured on the server.")

    try:
        # Supabase's legacy JWT secret signs HS256 tokens. Do not accept asymmetric
        # algorithms here: an HMAC secret must not be interpreted as an RSA/ECDSA key.
        payload = jwt.decode(
            token,
            key=secret,
            algorithms=["HS256"],
            options={"verify_signature": True, "verify_exp": True, "verify_aud": False},
        )
        if not payload.get("sub"):
            raise AuthenticationError("Token payload is missing the user identifier (sub).")
        return payload
    except AuthenticationError:
        raise
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
    """FastAPI dependency returning a verified JWT payload."""
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
