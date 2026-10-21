import pytest

from app.core.config import settings
from app.core.exceptions import AuthenticationError
from app.core.cognito_security import decode_cognito_access_token


def test_cognito_access_tokens_rejected_while_feature_disabled(monkeypatch):
    monkeypatch.setattr(settings, "COGNITO_ENABLED", False)
    with pytest.raises(AuthenticationError, match="not enabled"):
        decode_cognito_access_token("not-a-real-token")


def test_cognito_access_tokens_rejected_without_client_id(monkeypatch):
    monkeypatch.setattr(settings, "COGNITO_ENABLED", True)
    monkeypatch.setattr(settings, "COGNITO_APP_CLIENT_ID", "")
    with pytest.raises(AuthenticationError, match="app client is not configured"):
        decode_cognito_access_token("not-a-real-token")
