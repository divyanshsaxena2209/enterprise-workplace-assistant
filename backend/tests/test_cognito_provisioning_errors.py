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
    monkeypatch.setattr(auth, "create_supabase_auth_client", lambda: fake_client)
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
    monkeypatch.setattr(auth.settings, "COGNITO_MANAGEMENT_EMAIL_ALLOWLIST", "")

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
    monkeypatch.setattr(auth, "create_supabase_auth_client", lambda: fake_client)
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
    monkeypatch.setattr(auth.settings, "COGNITO_MANAGEMENT_EMAIL_ALLOWLIST", "")

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
    monkeypatch.setattr(auth, "create_supabase_auth_client", lambda: fake_client)
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



def test_allowlisted_management_signup_is_assigned_management_by_server(monkeypatch):
    from app.core.enums import UserRole

    profile = SimpleNamespace(
        id="allowlisted-profile-id",
        email="trusted.manager@example.test",
        role=UserRole.EMPLOYEE,
        is_active=True,
        is_management_verified=False,
    )
    fake_client = SimpleNamespace(
        auth=SimpleNamespace(
            admin=SimpleNamespace(
                get_user_by_id=lambda _profile_id: SimpleNamespace(
                    user=SimpleNamespace(email="trusted.manager@example.test")
                )
            )
        )
    )
    mappings = []
    updates = []
    audited = []

    class FakeProfiles:
        def __init__(self, _client):
            pass

        def get_by_email(self, _email):
            return profile

        def update(self, profile_id, payload):
            updates.append((profile_id, dict(payload)))
            profile.role = UserRole(payload["role"])
            profile.is_management_verified = payload["is_management_verified"]
            return profile

    class FakeMappings:
        def __init__(self, _client):
            pass

        def create_mapping(self, subject, profile_id):
            mappings.append((subject, profile_id))

    class FakeRequests:
        def __init__(self, _client):
            pass

        def mark_allowlisted_approved(self, profile_id):
            audited.append(profile_id)
            return {"profile_id": profile_id, "status": "APPROVED"}

        def submit(self, *_args, **_kwargs):
            raise AssertionError("Trusted allowlisted accounts should not queue for approval.")

    monkeypatch.setattr(
        auth.settings,
        "COGNITO_MANAGEMENT_EMAIL_ALLOWLIST",
        "other@example.test, trusted.manager@example.test",
    )
    monkeypatch.setattr(auth, "decode_cognito_id_token", lambda _token, _nonce: {
        "email": "trusted.manager@example.test",
        "sub": "trusted-cognito-sub",
    })
    monkeypatch.setattr(auth, "get_supabase_client", lambda: fake_client)
    monkeypatch.setattr(auth, "create_supabase_auth_client", lambda: fake_client)
    monkeypatch.setattr(auth, "ProfileRepository", FakeProfiles)
    monkeypatch.setattr(auth, "CognitoIdentityRepository", FakeMappings)
    monkeypatch.setattr(auth, "ManagementAccessRequestRepository", FakeRequests)

    body = CognitoLinkRequest(
        id_token="i" * 32,
        nonce="n" * 24,
        profile=CognitoSignupProfile(
            full_name="Trusted Manager",
            department="Engineering",
            job_title="Engineering Manager",
            requested_access_level="MANAGEMENT",
        ),
    )
    result = auth.link_cognito_identity(body)

    assert "Management access was assigned" in result.message
    assert profile.role == UserRole.MANAGEMENT
    assert profile.is_management_verified is True
    assert updates == [(
        "allowlisted-profile-id",
        {"role": "MANAGEMENT", "is_management_verified": True},
    )]
    assert mappings == [("trusted-cognito-sub", "allowlisted-profile-id")]
    assert audited == ["allowlisted-profile-id"]


def test_existing_allowlisted_employee_can_request_and_receive_management(monkeypatch):
    from app.core.enums import UserRole
    from app.routers import profile as profile_router

    employee = SimpleNamespace(
        id="existing-profile-id",
        email="trusted.manager@example.test",
        role=UserRole.EMPLOYEE,
    )
    updates = []
    audited = []
    client = object()

    class FakeProfiles:
        def __init__(self, _client):
            pass

        def update(self, profile_id, payload):
            updates.append((profile_id, dict(payload)))
            employee.role = UserRole.MANAGEMENT
            return employee

    class FakeRequests:
        def __init__(self, _client):
            pass

        def mark_allowlisted_approved(self, profile_id):
            audited.append(profile_id)
            return {"profile_id": profile_id, "requested_role": "MANAGEMENT", "status": "APPROVED"}

        def submit(self, *_args, **_kwargs):
            raise AssertionError("Allowlisted account should be granted access directly.")

    monkeypatch.setattr(
        profile_router.settings,
        "COGNITO_MANAGEMENT_EMAIL_ALLOWLIST",
        "trusted.manager@example.test",
    )
    monkeypatch.setattr(profile_router, "get_supabase_client", lambda: client)
    monkeypatch.setattr(profile_router, "ProfileRepository", FakeProfiles)
    monkeypatch.setattr(profile_router, "ManagementAccessRequestRepository", FakeRequests)

    result = profile_router.submit_management_access_request(
        profile_router.ManagementAccessRequestSubmit(),
        current_user=employee,
    )

    assert result["request"]["status"] == "APPROVED"
    assert "assigned by the trusted administrator configuration" in result["message"]
    assert updates == [(
        "existing-profile-id",
        {"role": "MANAGEMENT", "is_management_verified": True},
    )]
    assert audited == ["existing-profile-id"]



@pytest.mark.parametrize(
    ("selected_role", "expected_verified"),
    [("EMPLOYEE", False), ("MANAGEMENT", True)],
)
def test_staging_demo_role_selector_switches_application_role_without_allowlist(
    monkeypatch, selected_role, expected_verified
):
    """The login-page role choice only grants roles when the explicit staging demo flag is on."""
    from app.core.enums import UserRole

    # Start from the opposite role so each parameterized case verifies a real switch.
    starting_role = UserRole.MANAGEMENT if selected_role == "EMPLOYEE" else UserRole.EMPLOYEE
    profile = SimpleNamespace(
        id="demo-profile-id",
        email="demo.user@example.test",
        role=starting_role,
        is_active=True,
        is_management_verified=starting_role == UserRole.MANAGEMENT,
    )
    updates = []
    fake_client = SimpleNamespace(
        auth=SimpleNamespace(
            admin=SimpleNamespace(
                get_user_by_id=lambda _profile_id: SimpleNamespace(
                    user=SimpleNamespace(email="demo.user@example.test")
                )
            )
        )
    )

    class FakeProfiles:
        def __init__(self, _client):
            pass

        def get_by_email(self, _email):
            return profile

        def update(self, profile_id, payload):
            updates.append((profile_id, dict(payload)))
            profile.role = UserRole(payload["role"])
            profile.is_management_verified = payload["is_management_verified"]
            return profile

    class FakeMappings:
        def __init__(self, _client):
            pass

        def create_mapping(self, _subject, _profile_id):
            pass

    class FakeRequests:
        def __init__(self, _client):
            pass

        def submit(self, *_args, **_kwargs):
            raise AssertionError("Demo role selection must not create a pending request.")

        def mark_allowlisted_approved(self, *_args, **_kwargs):
            raise AssertionError("Demo role selection does not rely on an email allowlist.")

    monkeypatch.setattr(auth.settings, "ENVIRONMENT", "staging")
    monkeypatch.setattr(auth.settings, "COGNITO_ENABLED", True)
    monkeypatch.setattr(auth.settings, "COGNITO_DEMO_ROLE_SELECTION_ENABLED", True)
    monkeypatch.setattr(auth.settings, "COGNITO_MANAGEMENT_EMAIL_ALLOWLIST", "")
    monkeypatch.setattr(auth, "decode_cognito_id_token", lambda _token, _nonce: {
        "email": "demo.user@example.test",
        "sub": "demo-cognito-sub",
    })
    monkeypatch.setattr(auth, "get_supabase_client", lambda: fake_client)
    monkeypatch.setattr(auth, "create_supabase_auth_client", lambda: fake_client)
    monkeypatch.setattr(auth, "ProfileRepository", FakeProfiles)
    monkeypatch.setattr(auth, "CognitoIdentityRepository", FakeMappings)
    monkeypatch.setattr(auth, "ManagementAccessRequestRepository", FakeRequests)

    body = CognitoLinkRequest(
        id_token="i" * 32,
        nonce="n" * 24,
        requested_access_level=selected_role,
    )
    result = auth.link_cognito_identity(body)

    assert selected_role in result.message
    assert profile.role == UserRole(selected_role)
    assert profile.is_management_verified is expected_verified
    assert updates == [(
        "demo-profile-id",
        {"role": selected_role, "is_management_verified": expected_verified},
    )]


def test_demo_role_selector_cannot_grant_management_outside_staging(monkeypatch):
    monkeypatch.setattr(auth.settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(auth.settings, "COGNITO_ENABLED", True)
    monkeypatch.setattr(auth.settings, "COGNITO_DEMO_ROLE_SELECTION_ENABLED", True)
    monkeypatch.setattr(auth.settings, "COGNITO_MANAGEMENT_EMAIL_ALLOWLIST", "")
    assert auth.settings.cognito_demo_role_selection_enabled is False



def test_auth_service_keeps_auth_session_separate_from_database_client(monkeypatch):
    """Signup/login session state must not alter the privileged PostgREST client."""
    from app.services import auth_service as auth_service_module

    db_client = object()
    dedicated_auth_client = object()
    monkeypatch.setattr(
        auth_service_module,
        "create_supabase_auth_client",
        lambda: dedicated_auth_client,
    )

    service = auth_service_module.AuthService(db_client)

    assert service._auth is dedicated_auth_client
    assert service._repo._db is db_client
