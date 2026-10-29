"""Resolve verified bearer tokens to existing database-backed user profiles."""
import jwt

from app.core.exceptions import AuthenticationError
from app.core.security import decode_jwt, extract_user_id
from app.core.cognito_security import decode_cognito_access_token
from app.repositories.cognito_identity_repository import CognitoIdentityRepository
from app.repositories.profile_repository import ProfileRepository
from app.models.profile import ProfileModel


def resolve_profile_from_bearer_token(
    token: str,
    profile_repository: ProfileRepository,
    cognito_identity_repository: CognitoIdentityRepository,
) -> ProfileModel | None:
    """Resolve Supabase HS256 or mapped Cognito RS256 tokens.

    The token header is used only to select a strict verifier. Each verifier
    independently enforces its only allowed algorithm, issuer/key and claims.
    Application roles always come from the existing Supabase profiles row.
    """
    try:
        header = jwt.get_unverified_header(token)
    except jwt.InvalidTokenError as exc:
        raise AuthenticationError("Invalid authentication token.") from exc

    algorithm = header.get("alg")
    if algorithm == "HS256":
        claims = decode_jwt(token)
        profile_id = extract_user_id(claims)
    elif algorithm == "RS256":
        claims = decode_cognito_access_token(token)
        profile_id = cognito_identity_repository.get_profile_id(str(claims["sub"]))
        if not profile_id:
            return None
    else:
        raise AuthenticationError("Unsupported authentication token algorithm.")

    profile = profile_repository.get_by_id(profile_id)
    if profile is None or not profile.is_active:
        return None
    return profile
