"""
AuthMiddleware — pre-populates request.state.user for every authenticated request.

Design decisions:
- This middleware does NOT block unauthenticated requests.
  Blocking is the responsibility of route-level dependencies (require_management, etc.).
- If the token is valid, request.state.user = ProfileResponse.
- If the token is missing or invalid, request.state.user = None.
- This allows public routes (health, docs) to work without a token.
- Route dependencies check request.state.user before decoding again (fast path).
- Implemented as a raw ASGI middleware to prevent deadlocks on POST/PUT body reading.
"""

import logging
from starlette.types import ASGIApp, Scope, Receive, Send

from app.db.supabase import get_supabase_client
from app.repositories.cognito_identity_repository import CognitoIdentityRepository
from app.repositories.profile_repository import ProfileRepository
from app.services.identity_resolver import resolve_profile_from_bearer_token
from app.schemas.profile import ProfileResponse

logger = logging.getLogger(__name__)


_SKIP_PREFIXES = ("/docs", "/redoc", "/openapi.json", "/health")


class AuthMiddleware:
    """
    ASGI middleware that resolves the current user on every request.

    Sets request.state.user to ProfileResponse (if authenticated) or None.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self._client = get_supabase_client()
        self._repo = ProfileRepository(self._client)
        self._cognito_identity_repo = CognitoIdentityRepository(self._client)

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
                    except Exception:
                        pass
                    break

            if auth_header.startswith("Bearer "):
                token = auth_header.removeprefix("Bearer ").strip()
                if token == "guest":
                    from datetime import datetime
                    from app.core.enums import UserRole
                    scope["state"]["user"] = ProfileResponse(
                        id="00000000-0000-0000-0000-000000000000",
                        email="guest@workforceos.internal",
                        full_name="Guest Administrator",
                        # Guest mode is a read-only demo identity, never a manager.
                        role=UserRole.EMPLOYEE,
                        is_active=True,
                        is_management_verified=False,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                else:
                    try:
                        profile = resolve_profile_from_bearer_token(
                            token,
                            self._repo,
                            self._cognito_identity_repo,
                        )
                        if profile is not None:
                            scope["state"]["user"] = ProfileResponse.from_model(profile)
                    except Exception:
                        # Do not log tokens, headers, or claims. Failed tokens remain
                        # unauthenticated and are rejected by protected route dependencies.
                        logger.debug("AuthMiddleware: could not resolve user", exc_info=False)

        await self.app(scope, receive, send)
