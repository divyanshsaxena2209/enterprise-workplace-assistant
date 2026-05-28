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
    # Protected by require_role(["HR_ADMIN", "SUPER_ADMIN"])
    response = client.get("/api/v1/hiring/")
    assert response.status_code in [401, 403]
