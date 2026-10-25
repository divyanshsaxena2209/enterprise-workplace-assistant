"""
AuthMiddleware pre-populates request.state.user after JWT verification.

The middleware never grants access based on a magic guest token. Public routes
remain public; protected routes use route-level dependencies for authorization.
"""

import logging
from starlette.types import ASGIApp, Scope, Receive, Send

from app.core.security import decode_jwt, extract_user_id
from app.db.supabase import get_supabase_client
from app.repositories.profile_repository import ProfileRepository
from app.schemas.profile import ProfileResponse

logger = logging.getLogger(__name__)

_SKIP_PREFIXES = ("/docs", "/redoc", "/openapi.json", "/health")


class AuthMiddleware:
    """Resolve a valid user's profile when a verifiable bearer token is present."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self._client = get_supabase_client()
        self._repo = ProfileRepository(self._client)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        if "state" not in scope:
            scope["state"] = {}
        scope["state"]["user"] = None

        path = scope.get("path", "")
        if not any(path.startswith(prefix) for prefix in _SKIP_PREFIXES):
            auth_header = ""
            for key, val in scope.get("headers", []):
                if key == b"authorization":
                    try:
                        auth_header = val.decode("latin1")
                    except UnicodeDecodeError:
                        auth_header = ""
                    break

            if auth_header.startswith("Bearer "):
                token = auth_header.removeprefix("Bearer ").strip()
                if token:
                    try:
                        payload = decode_jwt(token)
                        user_id = extract_user_id(payload)
                        profile = self._repo.get_by_id(user_id)
                        if profile is not None and profile.is_active:
                            scope["state"]["user"] = ProfileResponse.from_model(profile)
                    except Exception:
                        # Do not log the token or exception details, which may contain
                        # sensitive auth context. Protected dependencies will return 401.
                        logger.debug("AuthMiddleware: token could not be resolved")

        await self.app(scope, receive, send)
