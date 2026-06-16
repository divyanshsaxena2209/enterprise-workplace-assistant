"""
AuthMiddleware — pre-populates request.state.user for every authenticated request.

Design decisions:
- This middleware does NOT block unauthenticated requests.
  Blocking is the responsibility of route-level dependencies (require_management, etc.).
- If the token is valid, request.state.user = ProfileResponse.
- If the token is missing or invalid, request.state.user = None.
- This allows public routes (health, docs) to work without a token.
- Route dependencies check request.state.user before decoding again (fast path).
"""

import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from app.core.security import decode_jwt, extract_user_id
from app.db.supabase import get_supabase_client
from app.repositories.profile_repository import ProfileRepository
from app.schemas.profile import ProfileResponse

logger = logging.getLogger(__name__)

# Routes that should skip profile loading entirely (even if token is present).
_SKIP_PREFIXES = ("/docs", "/redoc", "/openapi.json", "/health")


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Starlette BaseHTTPMiddleware that resolves the current user on every request.

    Sets request.state.user to ProfileResponse (if authenticated) or None.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self._client = get_supabase_client()
        self._repo = ProfileRepository(self._client)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Default — no user context.
        request.state.user = None

        # Skip middleware work for docs / health endpoints.
        if any(request.url.path.startswith(prefix) for prefix in _SKIP_PREFIXES):
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.removeprefix("Bearer ").strip()
            try:
                payload = decode_jwt(token)
                user_id = extract_user_id(payload)
                profile = self._repo.get_by_id(user_id)
                if profile and profile.is_active:
                    request.state.user = ProfileResponse.from_model(profile)
            except Exception:
                # Silently swallow — the dependency will raise the proper error
                # when the route is protected. Public routes continue normally.
                logger.debug(
                    "AuthMiddleware: could not resolve user for %s %s",
                    request.method,
                    request.url.path,
                    exc_info=False,
                )

        return await call_next(request)
