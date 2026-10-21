from datetime import datetime

import pytest
from pydantic import ValidationError

from app.core.enums import UserRole
from app.core.exceptions import AuthorizationError, NotFoundError
from app.models.profile import ProfileModel
from app.routers import profile as profile_router
from app.schemas.profile import ProfileResponse


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
