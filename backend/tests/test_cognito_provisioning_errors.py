"""Regression tests for safe Cognito account provisioning error classification."""

from types import SimpleNamespace

import pytest

from app.core.exceptions import DatabaseError
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


def test_management_access_choice_creates_request_without_elevating_profile(monkeypatch):
    from app.core.enums import UserRole

    employee_profile = SimpleNamespace(
        id="employee-profile-id",
        email="requester@example.test",
        role=UserRole.EMPLOYEE,
        is_active=True,
    )
    fake_client = SimpleNamespace(
        auth=SimpleNamespace(
            admin=SimpleNamespace(
                get_user_by_id=lambda _profile_id: SimpleNamespace(
                    user=SimpleNamespace(email="requester@example.test")
                )
            )
        )
    )
    mapping_calls = []
    request_calls = []

    class FakeProfiles:
        def __init__(self, _client):
            pass

        def get_by_email(self, email):
            assert email == "requester@example.test"
            return employee_profile

    class FakeMappings:
        def __init__(self, _client):
            pass

        def create_mapping(self, subject, profile_id):
            mapping_calls.append((subject, profile_id))

    class FakeManagementRequests:
        def __init__(self, _client):
            pass

        def submit(self, profile_id, request_note=None):
            request_calls.append((profile_id, request_note))
            return {"profile_id": profile_id, "status": "PENDING", "requested_role": "MANAGEMENT"}

    monkeypatch.setattr(auth, "decode_cognito_id_token", lambda _token, _nonce: {
        "email": "requester@example.test",
        "sub": "synthetic-cognito-sub",
    })
    monkeypatch.setattr(auth, "get_supabase_client", lambda: fake_client)
    monkeypatch.setattr(auth, "ProfileRepository", FakeProfiles)
    monkeypatch.setattr(auth, "CognitoIdentityRepository", FakeMappings)
    monkeypatch.setattr(auth, "ManagementAccessRequestRepository", FakeManagementRequests)

    body = CognitoLinkRequest(
        id_token="i" * 32,
        nonce="n" * 24,
        profile=CognitoSignupProfile(
            full_name="Requested Manager",
            department="Engineering",
            job_title="Team Lead",
            requested_access_level="MANAGEMENT",
        ),
    )
    result = auth.link_cognito_identity(body)

    assert result.message.startswith("Cognito account linked")
    assert "pending administrator approval" in result.message
    assert employee_profile.role == UserRole.EMPLOYEE
    assert mapping_calls == [("synthetic-cognito-sub", "employee-profile-id")]
    assert request_calls == [("employee-profile-id", None)]


def test_employee_choice_does_not_create_management_request(monkeypatch):
    from app.core.enums import UserRole

    employee_profile = SimpleNamespace(
        id="employee-profile-id",
        email="employee@example.test",
        role=UserRole.EMPLOYEE,
        is_active=True,
    )
    fake_client = SimpleNamespace(
        auth=SimpleNamespace(
            admin=SimpleNamespace(
                get_user_by_id=lambda _profile_id: SimpleNamespace(
                    user=SimpleNamespace(email="employee@example.test")
                )
            )
        )
    )
    request_calls = []

    class FakeProfiles:
        def __init__(self, _client):
            pass

        def get_by_email(self, _email):
            return employee_profile

    class FakeMappings:
        def __init__(self, _client):
            pass

        def create_mapping(self, _subject, _profile_id):
            pass

    class FakeManagementRequests:
        def __init__(self, _client):
            pass

        def submit(self, profile_id, request_note=None):
            request_calls.append((profile_id, request_note))
            return {"status": "PENDING"}

    monkeypatch.setattr(auth, "decode_cognito_id_token", lambda _token, _nonce: {
        "email": "employee@example.test",
        "sub": "synthetic-cognito-sub",
    })
    monkeypatch.setattr(auth, "get_supabase_client", lambda: fake_client)
    monkeypatch.setattr(auth, "ProfileRepository", FakeProfiles)
    monkeypatch.setattr(auth, "CognitoIdentityRepository", FakeMappings)
    monkeypatch.setattr(auth, "ManagementAccessRequestRepository", FakeManagementRequests)

    body = CognitoLinkRequest(
        id_token="i" * 32,
        nonce="n" * 24,
        profile=CognitoSignupProfile(
            full_name="New Employee",
            department="Engineering",
            job_title="Engineer",
            requested_access_level="EMPLOYEE",
        ),
    )
    result = auth.link_cognito_identity(body)

    assert result.message == "Cognito identity linked to the existing profile."
    assert request_calls == []
