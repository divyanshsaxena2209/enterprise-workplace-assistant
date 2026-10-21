from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from app.core import cognito_security
from app.core.config import settings
from app.core.exceptions import AuthenticationError


REGION = "ap-south-1"
POOL_ID = "ap-south-1_testPool"
CLIENT_ID = "test-public-client"
ISSUER = f"https://cognito-idp.{REGION}.amazonaws.com/{POOL_ID}"
EXPECTED_NONCE = "unit-test-oauth-nonce-value"


@pytest.fixture
def signing_keys(monkeypatch):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    wrong_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    class FakeJwksClient:
        def __init__(self, key):
            self.key = key

        def get_signing_key_from_jwt(self, token):
            return SimpleNamespace(key=self.key)

    monkeypatch.setattr(settings, "COGNITO_ENABLED", True)
    monkeypatch.setattr(settings, "COGNITO_REGION", REGION)
    monkeypatch.setattr(settings, "COGNITO_USER_POOL_ID", POOL_ID)
    monkeypatch.setattr(settings, "COGNITO_APP_CLIENT_ID", CLIENT_ID)
    monkeypatch.setattr(cognito_security, "_jwks_client", lambda: FakeJwksClient(private_key.public_key()))
    return private_key, wrong_private_key


def make_token(private_key, **overrides):
    now = datetime.now(timezone.utc)
    claims = {
        "iss": ISSUER,
        "sub": "cognito-user-sub",
        "client_id": CLIENT_ID,
        "token_use": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=5)).timestamp()),
        "scope": "openid email",
    }
    claims.update(overrides)
    return jwt.encode(claims, private_key, algorithm="RS256", headers={"kid": "unit-test-key"})


def make_id_token(private_key, **overrides):
    now = datetime.now(timezone.utc)
    claims = {
        "iss": ISSUER,
        "sub": "cognito-user-sub",
        "aud": CLIENT_ID,
        "token_use": "id",
        "email": "employee@example.com",
        "email_verified": True,
        "nonce": EXPECTED_NONCE,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=5)).timestamp()),
    }
    claims.update(overrides)
    return jwt.encode(claims, private_key, algorithm="RS256", headers={"kid": "unit-test-key"})


def test_cognito_tokens_rejected_while_feature_disabled(monkeypatch):
    monkeypatch.setattr(settings, "COGNITO_ENABLED", False)
    with pytest.raises(AuthenticationError, match="not enabled"):
        cognito_security.decode_cognito_access_token("not-a-real-token")


def test_cognito_tokens_rejected_without_client_id(monkeypatch):
    monkeypatch.setattr(settings, "COGNITO_ENABLED", True)
    monkeypatch.setattr(settings, "COGNITO_APP_CLIENT_ID", "")
    with pytest.raises(AuthenticationError, match="app client is not configured"):
        cognito_security.decode_cognito_access_token("not-a-real-token")


def test_accepts_valid_signed_access_token(signing_keys):
    private_key, _ = signing_keys
    claims = cognito_security.decode_cognito_access_token(make_token(private_key))
    assert claims["sub"] == "cognito-user-sub"
    assert claims["token_use"] == "access"


def test_rejects_invalid_signature(signing_keys):
    _, wrong_private_key = signing_keys
    with pytest.raises(AuthenticationError, match="Invalid Cognito access token"):
        cognito_security.decode_cognito_access_token(make_token(wrong_private_key))


def test_rejects_wrong_issuer(signing_keys):
    private_key, _ = signing_keys
    with pytest.raises(AuthenticationError, match="Invalid Cognito access token"):
        cognito_security.decode_cognito_access_token(
            make_token(private_key, iss="https://attacker.example")
        )


def test_rejects_expired_token(signing_keys):
    private_key, _ = signing_keys
    past = datetime.now(timezone.utc) - timedelta(minutes=5)
    with pytest.raises(AuthenticationError, match="Invalid Cognito access token"):
        cognito_security.decode_cognito_access_token(make_token(private_key, exp=int(past.timestamp())))


def test_rejects_id_token_instead_of_access_token(signing_keys):
    private_key, _ = signing_keys
    with pytest.raises(AuthenticationError, match="A Cognito access token is required"):
        cognito_security.decode_cognito_access_token(make_token(private_key, token_use="id"))


def test_rejects_token_for_different_app_client(signing_keys):
    private_key, _ = signing_keys
    with pytest.raises(AuthenticationError, match="different Cognito app client"):
        cognito_security.decode_cognito_access_token(make_token(private_key, client_id="other-client"))


def test_rejects_missing_subject(signing_keys):
    private_key, _ = signing_keys
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "iss": ISSUER,
            "client_id": CLIENT_ID,
            "token_use": "access",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=5)).timestamp()),
        },
        private_key,
        algorithm="RS256",
        headers={"kid": "unit-test-key"},
    )
    with pytest.raises(AuthenticationError, match="Invalid Cognito access token"):
        cognito_security.decode_cognito_access_token(token)


def test_accepts_valid_verified_id_token_for_account_linking(signing_keys):
    private_key, _ = signing_keys
    claims = cognito_security.decode_cognito_id_token(make_id_token(private_key), EXPECTED_NONCE)
    assert claims["sub"] == "cognito-user-sub"
    assert claims["email"] == "employee@example.com"
    assert claims["email_verified"] is True


def test_rejects_unverified_email_for_account_linking(signing_keys):
    private_key, _ = signing_keys
    with pytest.raises(AuthenticationError, match="Verify the Cognito email"):
        cognito_security.decode_cognito_id_token(
            make_id_token(private_key, email_verified=False), EXPECTED_NONCE
        )


def test_rejects_id_token_for_another_app_client(signing_keys):
    private_key, _ = signing_keys
    with pytest.raises(AuthenticationError, match="Invalid Cognito ID token"):
        cognito_security.decode_cognito_id_token(
            make_id_token(private_key, aud="another-client"), EXPECTED_NONCE
        )


def test_rejects_access_token_for_account_linking(signing_keys):
    private_key, _ = signing_keys
    with pytest.raises(AuthenticationError, match="A Cognito ID token is required"):
        cognito_security.decode_cognito_id_token(
            make_id_token(private_key, token_use="access"), EXPECTED_NONCE
        )


def test_rejects_expired_id_token(signing_keys):
    private_key, _ = signing_keys
    past = datetime.now(timezone.utc) - timedelta(minutes=5)
    with pytest.raises(AuthenticationError, match="Invalid Cognito ID token"):
        cognito_security.decode_cognito_id_token(
            make_id_token(private_key, exp=int(past.timestamp())), EXPECTED_NONCE
        )


def test_rejects_wrong_oauth_nonce_for_account_linking(signing_keys):
    private_key, _ = signing_keys
    with pytest.raises(AuthenticationError, match="nonce does not match"):
        cognito_security.decode_cognito_id_token(
            make_id_token(private_key), "different-oauth-nonce-value"
        )
