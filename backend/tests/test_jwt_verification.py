from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.core.config import settings
from app.core.exceptions import AuthenticationError
from app.core.security import decode_jwt


def _token(secret: str, *, subject: str = "user-123", expires_in: int = 300) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": subject, "iat": now, "exp": now + timedelta(seconds=expires_in)},
        secret,
        algorithm="HS256",
    )


def test_decode_jwt_accepts_valid_signed_token(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", "test-secret-for-unit-tests-only")
    token = _token(settings.SUPABASE_JWT_SECRET)
    assert decode_jwt(token)["sub"] == "user-123"


def test_decode_jwt_rejects_tampered_signature(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", "test-secret-for-unit-tests-only")
    token = _token("a-different-secret")
    with pytest.raises(AuthenticationError):
        decode_jwt(token)


def test_decode_jwt_fails_closed_when_secret_missing(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", "")
    token = jwt.encode({"sub": "attacker"}, key="unused", algorithm="HS256")
    with pytest.raises(AuthenticationError):
        decode_jwt(token)


def test_decode_jwt_rejects_expired_token(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", "test-secret-for-unit-tests-only")
    token = _token(settings.SUPABASE_JWT_SECRET, expires_in=-30)
    with pytest.raises(AuthenticationError):
        decode_jwt(token)
