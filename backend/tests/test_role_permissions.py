from types import SimpleNamespace

import pytest

from app.core.enums import UserRole
from app.core.exceptions import AuthorizationError
from app.services.auth_service import AuthService
from app.dependencies.auth import (
    require_employee,
    require_management,
    require_management_or_employee,
)


GUEST_ID = "00000000-0000-0000-0000-000000000000"
MANAGER = SimpleNamespace(id="manager-1", role=UserRole.MANAGEMENT)
EMPLOYEE = SimpleNamespace(id="employee-1", role=UserRole.EMPLOYEE)
GUEST = SimpleNamespace(id=GUEST_ID, role=UserRole.EMPLOYEE)


def test_management_can_pass_management_guard():
    assert require_management(MANAGER) is MANAGER


def test_employee_cannot_perform_management_tasks():
    with pytest.raises(AuthorizationError):
        require_management(EMPLOYEE)


def test_employee_can_pass_employee_guard():
    assert require_employee(EMPLOYEE) is EMPLOYEE


def test_management_cannot_submit_as_employee():
    with pytest.raises(AuthorizationError):
        require_employee(MANAGER)


def test_guest_cannot_inherit_management_access():
    with pytest.raises(AuthorizationError):
        require_management(GUEST)


def test_guest_cannot_use_write_guard():
    with pytest.raises(AuthorizationError):
        require_management_or_employee(GUEST)


@pytest.mark.parametrize("identity", [MANAGER, EMPLOYEE])
def test_real_app_roles_can_use_shared_app_guard(identity):
    assert require_management_or_employee(identity) is identity


def test_public_signup_cannot_self_assign_management_role():
    service = AuthService.__new__(AuthService)
    request = SimpleNamespace(role=UserRole.MANAGEMENT)
    with pytest.raises(AuthorizationError):
        service.signup(request)
