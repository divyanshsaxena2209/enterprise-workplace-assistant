"""Security regression tests for authentication and knowledge-document RBAC."""

import jwt
import pytest

from app.core import security
from app.core.config import settings
from app.core.exceptions import AuthenticationError


def test_decode_jwt_rejects_missing_verification_secret(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", "")
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    with pytest.raises(AuthenticationError):
        security.decode_jwt("not-a-jwt")


def test_decode_jwt_rejects_invalid_signature(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", "expected-secret")
    forged = jwt.encode({"sub": "00000000-0000-0000-0000-000000000001"}, "other-secret", algorithm="HS256")
    with pytest.raises(AuthenticationError):
        security.decode_jwt(forged)


def test_decode_jwt_rejects_expired_token(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", "expected-secret")
    expired = jwt.encode(
        {"sub": "00000000-0000-0000-0000-000000000001", "exp": 1},
        "expected-secret",
        algorithm="HS256",
    )
    with pytest.raises(AuthenticationError):
        security.decode_jwt(expired)


def test_decode_jwt_accepts_valid_signed_token(monkeypatch):
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", "expected-secret")
    token = jwt.encode(
        {"sub": "00000000-0000-0000-0000-000000000001", "exp": 4102444800},
        "expected-secret",
        algorithm="HS256",
    )
    assert security.decode_jwt(token)["sub"] == "00000000-0000-0000-0000-000000000001"
