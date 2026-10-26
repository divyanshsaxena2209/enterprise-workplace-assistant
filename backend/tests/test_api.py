from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_current_user, require_role

client = TestClient(app)

def test_health_check():
    """
    Tests the main health check endpoint.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "Enterprise Workplace Assistant API",
        "version": "1.0.0"
    }

def test_unauthorized_access():
    """
    Verifies that calling a protected route without a JWT bearer token returns 403 / 401.
    """
    
    response = client.get("/api/v1/hiring/")
    assert response.status_code in [401, 403]


def test_create_application_allows_management_and_employee_accounts():
    """Guard the management resume-ingestion flow against employee-only RBAC regressions."""
    from app.dependencies.auth import require_management_or_employee
    from app.routers.applications import router as applications_router

    route = next(
        route for route in applications_router.routes
        if getattr(route, "endpoint", None).__name__ == "create_application"
    )
    assert any(
        dependency.call is require_management_or_employee
        for dependency in route.dependant.dependencies
    )
