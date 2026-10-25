from datetime import datetime
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.core.enums import UserRole
from app.core.exceptions import AuthorizationError, NotFoundError
from app.schemas.auth import SignupRequest
from app.services import auth_service as auth_service_module
from app.services.auth_service import AuthService
from app.models.profile import ProfileModel
from app.routers import profile as profile_router
from app.schemas.profile import ProfileResponse, ProfileUpdateRequest


PROFILE_ID = "11111111-1111-4111-8111-111111111111"
MANAGER_ID = "22222222-2222-4222-8222-222222222222"


def make_profile(profile_id: str, role: UserRole, employee_id=None) -> ProfileModel:
    now = datetime.utcnow()
    return ProfileModel(
        id=profile_id,
        email=f"{profile_id[:8]}@example.com",
        full_name="Test User",
        role=role,
        is_active=True,
        is_management_verified=role == UserRole.MANAGEMENT,
        created_at=now,
        updated_at=now,
        employee_id=employee_id,
    )


def make_response(profile: ProfileModel) -> ProfileResponse:
    return ProfileResponse.from_model(profile)


class FakeProfileRepository:
    def __init__(self, profile):
        self.profile = profile
        self.updates = []

    def get_by_id(self, profile_id):
        return self.profile if self.profile and self.profile.id == profile_id else None

    def update(self, profile_id, changes):
        self.updates.append((profile_id, changes))
        for key, value in changes.items():
            setattr(self.profile, key, value)
        return self.profile


@pytest.fixture
def manager():
    return make_response(make_profile(MANAGER_ID, UserRole.MANAGEMENT))


def test_management_can_assign_an_employee_id(monkeypatch, manager):
    employee = make_profile(PROFILE_ID, UserRole.EMPLOYEE)
    repository = FakeProfileRepository(employee)
    monkeypatch.setattr(profile_router, "get_supabase_client", lambda: object())
    monkeypatch.setattr(profile_router, "ProfileRepository", lambda _client: repository)

    result = profile_router.assign_employee_id(
        PROFILE_ID,
        profile_router.EmployeeIdUpdateRequest(employee_id="SS-54321"),
        manager,
    )

    assert result.employee_id == "SS-54321"
    assert repository.updates == [(PROFILE_ID, {"employee_id": "SS-54321"})]


def test_management_cannot_assign_employee_id_to_another_manager(monkeypatch, manager):
    target_manager = make_profile(PROFILE_ID, UserRole.MANAGEMENT)
    repository = FakeProfileRepository(target_manager)
    monkeypatch.setattr(profile_router, "get_supabase_client", lambda: object())
    monkeypatch.setattr(profile_router, "ProfileRepository", lambda _client: repository)

    with pytest.raises(AuthorizationError):
        profile_router.assign_employee_id(
            PROFILE_ID,
            profile_router.EmployeeIdUpdateRequest(employee_id="SS-54321"),
            manager,
        )

    assert repository.updates == []


def test_missing_target_profile_is_rejected(monkeypatch, manager):
    repository = FakeProfileRepository(None)
    monkeypatch.setattr(profile_router, "get_supabase_client", lambda: object())
    monkeypatch.setattr(profile_router, "ProfileRepository", lambda _client: repository)

    with pytest.raises(NotFoundError):
        profile_router.assign_employee_id(
            PROFILE_ID,
            profile_router.EmployeeIdUpdateRequest(employee_id="SS-54321"),
            manager,
        )


@pytest.mark.parametrize("value", ["MANAGER", "SS-1234", "SS-123456", "ss-12345", "12345678"])
def test_employee_id_must_match_expected_format(value):
    with pytest.raises(ValidationError):
        profile_router.EmployeeIdUpdateRequest(employee_id=value)



def test_public_signup_ignores_caller_supplied_employee_id(monkeypatch):
    class FakeAuth:
        def __init__(self):
            self.signup_payload = None

        def sign_up(self, payload):
            self.signup_payload = payload
            return SimpleNamespace(
                session=SimpleNamespace(
                    access_token="test-access-token",
                    refresh_token="test-refresh-token",
                    expires_in=3600,
                ),
                user=SimpleNamespace(id=PROFILE_ID),
            )

    class FakeClient:
        def __init__(self):
            self.auth = FakeAuth()

    class FakeSignupRepository:
        def __init__(self):
            self.profile = make_profile(PROFILE_ID, UserRole.EMPLOYEE, "EMP-000123")
            self.upsert_payload = None

        def get_by_email(self, _email):
            return None

        def upsert(self, payload):
            self.upsert_payload = payload
            return self.profile

    auth_client = FakeClient()
    database_client = object()
    monkeypatch.setattr(
        auth_service_module,
        "create_supabase_auth_client",
        lambda: auth_client,
    )
    repository = FakeSignupRepository()
    monkeypatch.setattr(
        auth_service_module,
        "ProfileRepository",
        lambda _client: repository,
    )

    # Pydantic ignores unknown extra fields; the service must also avoid copying
    # that untrusted value into Auth metadata or the profile row.
    request = SignupRequest.model_validate({
        "full_name": "Test Employee",
        "email": "test.employee@example.com",
        "password": "Password123",
        "employee_id": "SPOOF-1",
    })
    assert "employee_id" not in SignupRequest.model_fields

    response = AuthService(database_client).signup(request)

    metadata = auth_client.auth.signup_payload["options"]["data"]
    assert "employee_id" not in metadata
    assert "employee_id" not in repository.upsert_payload
    assert response.user.employee_id == "EMP-000123"


def test_profile_patch_and_employee_id_routes_are_registered_to_their_handlers():
    route_handlers = {
        (route.path, method): route.endpoint.__name__
        for route in profile_router.router.routes
        for method in getattr(route, "methods", set())
    }

    assert route_handlers[("/profile", "PATCH")] == "update_profile"
    assert route_handlers[("/profile/employees/{profile_id}/department", "PATCH")] == "assign_employee_department"
    assert route_handlers[
        ("/profile/employees/{profile_id}/employee-id", "PATCH")
    ] == "assign_employee_id"



def test_self_service_profile_patch_cannot_set_department():
    with pytest.raises(ValidationError):
        ProfileUpdateRequest.model_validate(
            {"full_name": "Test Employee", "department": "Human Resources"}
        )


def test_management_can_assign_employee_department(monkeypatch, manager):
    employee = make_profile(PROFILE_ID, UserRole.EMPLOYEE)
    repository = FakeProfileRepository(employee)
    monkeypatch.setattr(profile_router, "get_supabase_client", lambda: object())
    monkeypatch.setattr(profile_router, "ProfileRepository", lambda _client: repository)

    result = profile_router.assign_employee_department(
        PROFILE_ID,
        profile_router.DepartmentUpdateRequest(department=" Human Resources "),
        manager,
    )

    assert result.department == "Human Resources"
    assert repository.updates == [(PROFILE_ID, {"department": "Human Resources"})]


def test_management_cannot_assign_department_to_another_manager(monkeypatch, manager):
    target_manager = make_profile(PROFILE_ID, UserRole.MANAGEMENT)
    repository = FakeProfileRepository(target_manager)
    monkeypatch.setattr(profile_router, "get_supabase_client", lambda: object())
    monkeypatch.setattr(profile_router, "ProfileRepository", lambda _client: repository)

    with pytest.raises(AuthorizationError):
        profile_router.assign_employee_department(
            PROFILE_ID,
            profile_router.DepartmentUpdateRequest(department="Engineering"),
            manager,
        )

    assert repository.updates == []


def test_department_assignment_endpoint_is_management_only():
    from app.dependencies.auth import require_management

    route = next(
        route for route in profile_router.router.routes
        if route.path == "/profile/employees/{profile_id}/department"
        and "PATCH" in (route.methods or set())
    )
    assert any(
        dependency.call is require_management
        for dependency in route.dependant.dependencies
    )


@pytest.mark.parametrize(
    "timestamp",
    [
        "2026-10-25T16:07:10.36298+00:00",
        "2026-10-25T16:07:10.36298Z",
    ],
)
def test_profile_model_parses_supabase_fractional_timestamps_on_python310(timestamp):
    """Supabase timestamps with 5 fractional digits must not 500 profile lookup."""
    profile = ProfileModel.from_dict(
        {
            "id": PROFILE_ID,
            "email": "timestamp@example.com",
            "full_name": "Timestamp User",
            "role": "MANAGEMENT",
            "is_active": True,
            "is_management_verified": True,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
    )

    assert profile.created_at.microsecond == 362980
    assert profile.updated_at.microsecond == 362980
    assert profile.created_at.utcoffset() is not None
