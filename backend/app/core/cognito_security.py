"""Cognito access-token verification groundwork; not wired into auth yet."""
from functools import lru_cache
from typing import Any

import jwt
from jwt import PyJWKClient

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
    """Validate signature, issuer, expiry, token type, and app client ID."""
    if not settings.COGNITO_ENABLED:
        raise AuthenticationError("Cognito authentication is not enabled.")
    if not settings.COGNITO_APP_CLIENT_ID:
        raise AuthenticationError("Cognito app client is not configured.")

    issuer = (
        f"https://cognito-idp.{settings.COGNITO_REGION}.amazonaws.com/"
        f"{settings.COGNITO_USER_POOL_ID}"
    )
    try:
        key = _jwks_client().get_signing_key_from_jwt(token).key
        claims = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            issuer=issuer,
            options={"verify_signature": True, "verify_exp": True, "verify_iss": True, "verify_aud": False},
        )
        if claims.get("token_use") != "access":
            raise AuthenticationError("A Cognito access token is required.")
        if claims.get("client_id") != settings.COGNITO_APP_CLIENT_ID:
            raise AuthenticationError("Token was issued to a different Cognito app client.")
        if not claims.get("sub"):
            raise AuthenticationError("Cognito token is missing its subject.")
        return claims
    except AuthenticationError:
        raise
    except (jwt.InvalidTokenError, jwt.PyJWKClientError, ValueError) as exc:
        raise AuthenticationError("Invalid Cognito access token.") from exc
