"""Regression tests for safe Cognito account provisioning error classification."""

from types import SimpleNamespace

import pytest

from app.core.exceptions import ConflictError, DatabaseError
from app.routers import auth
from app.schemas.auth import CognitoLinkRequest, CognitoSignupProfile


class FakeProfileRepository:
    def __init__(self, _client):
        pass

    def get_by_email(self, _email):
        # Simulate an admin.create_user failure where the auth trigger did not
        # create an application profile either.
        return None


def test_shadow_user_creation_failure_is_not_mislabeled_as_conflict(monkeypatch):
    class FakeAdmin:
        def create_user(self, _payload):
            raise RuntimeError("synthetic admin API failure")

    fake_client = SimpleNamespace(auth=SimpleNamespace(admin=FakeAdmin()))
    monkeypatch.setattr(
        auth,
        "decode_cognito_id_token",
        lambda _token, _nonce: {
            "email": "new.employee@example.test",
            "sub": "synthetic-cognito-sub",
        },
    )
    monkeypatch.setattr(auth, "get_supabase_client", lambda: fake_client)
    monkeypatch.setattr(auth, "ProfileRepository", FakeProfileRepository)

    body = CognitoLinkRequest(
        id_token="i" * 32,
        nonce="n" * 24,
        profile=CognitoSignupProfile(
            full_name="New Employee",
            department="Engineering",
            job_title="Engineer",
        ),
    )

    with pytest.raises(DatabaseError, match="Could not provision the employee profile"):
        auth.link_cognito_identity(body)
