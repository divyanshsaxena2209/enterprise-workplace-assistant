"""Cognito access-token verification groundwork; not wired into auth yet."""
from functools import lru_cache
from typing import Any

import jwt
from jwt import PyJWKClient
from jwt.exceptions import InvalidTokenError, PyJWKClientError

from app.core.config import settings
from app.core.exceptions import AuthenticationError


@lru_cache(maxsize=1)
def _jwks_client() -> PyJWKClient:
    if not settings.COGNITO_REGION or not settings.COGNITO_USER_POOL_ID:
        raise AuthenticationError("Cognito token verification is not configured.")
    url = (
        f"https://cognito-idp.{settings.COGNITO_REGION}.amazonaws.com/"
        f"{settings.COGNITO_USER_POOL_ID}/.well-known/jwks.json"
    )
    return PyJWKClient(url, cache_keys=True)


def decode_cognito_access_token(token: str) -> dict[str, Any]:
    """Validate signature, issuer, expiry, required claims, token type, and app client ID."""
    if not settings.COGNITO_ENABLED:
        raise AuthenticationError("Cognito authentication is not enabled.")
    if not settings.COGNITO_APP_CLIENT_ID:
        raise AuthenticationError("Cognito app client is not configured.")

    issuer = (
        f"https://cognito-idp.{settings.COGNITO_REGION}.amazonaws.com/"
        f"{settings.COGNITO_USER_POOL_ID}"
    )
    try:
        signing_key = _jwks_client().get_signing_key_from_jwt(token).key
        claims = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            issuer=issuer,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iss": True,
                "verify_aud": False,
                "require": ["exp", "iss", "sub", "token_use", "client_id"],
            },
        )
        if claims.get("token_use") != "access":
            raise AuthenticationError("A Cognito access token is required.")
        if claims.get("client_id") != settings.COGNITO_APP_CLIENT_ID:
            raise AuthenticationError("Token was issued to a different Cognito app client.")
        return claims
    except AuthenticationError:
        raise
    except (InvalidTokenError, PyJWKClientError, ValueError, TypeError) as exc:
        raise AuthenticationError("Invalid Cognito access token.") from exc


def decode_cognito_id_token(token: str) -> dict[str, Any]:
    """Verify a Cognito ID token for explicit account linking; not an API bearer token."""
    if not settings.COGNITO_ENABLED:
        raise AuthenticationError("Cognito authentication is not enabled.")
    if not settings.COGNITO_APP_CLIENT_ID:
        raise AuthenticationError("Cognito app client is not configured.")

    issuer = (
        f"https://cognito-idp.{settings.COGNITO_REGION}.amazonaws.com/"
        f"{settings.COGNITO_USER_POOL_ID}"
    )
    try:
        signing_key = _jwks_client().get_signing_key_from_jwt(token).key
        claims = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            issuer=issuer,
            audience=settings.COGNITO_APP_CLIENT_ID,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iss": True,
                "verify_aud": True,
                "require": ["exp", "iss", "sub", "aud", "token_use", "email", "email_verified"],
            },
        )
        if claims.get("token_use") != "id":
            raise AuthenticationError("A Cognito ID token is required for account linking.")
        if claims.get("email_verified") is not True:
            raise AuthenticationError("Verify the Cognito email address before linking accounts.")
        if not isinstance(claims.get("email"), str) or not claims["email"].strip():
            raise AuthenticationError("Cognito ID token does not contain a verified email.")
        return claims
    except AuthenticationError:
        raise
    except (InvalidTokenError, PyJWKClientError, ValueError, TypeError) as exc:
        raise AuthenticationError("Invalid Cognito ID token.") from exc
