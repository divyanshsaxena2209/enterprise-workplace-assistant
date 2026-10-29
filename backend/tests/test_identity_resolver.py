from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from app.core.config import settings
from app.core.exceptions import AuthenticationError
from app.services import identity_resolver


class FakeProfileRepository:
    def __init__(self, profiles):
        self.profiles = profiles
        self.lookups = []

    def get_by_id(self, user_id):
        self.lookups.append(user_id)
        return self.profiles.get(user_id)


class FakeCognitoMappingRepository:
    def __init__(self, mappings):
        self.mappings = mappings
        self.lookups = []

    def get_profile_id(self, cognito_sub):
        self.lookups.append(cognito_sub)
        return self.mappings.get(cognito_sub)


def _profile(profile_id, role="EMPLOYEE", active=True):
    return SimpleNamespace(id=profile_id, role=role, is_active=active)


def test_supabase_hs256_token_keeps_existing_profile_resolution(monkeypatch):
    secret = "unit-test-supabase-secret"
    monkeypatch.setattr(settings, "SUPABASE_JWT_SECRET", secret)
    token = jwt.encode({"sub": "existing-profile-id", "exp": 4102444800}, secret, algorithm="HS256")
    profiles = FakeProfileRepository({"existing-profile-id": _profile("existing-profile-id")})
    mappings = FakeCognitoMappingRepository({})

    resolved = identity_resolver.resolve_profile_from_bearer_token(token, profiles, mappings)

    assert resolved.id == "existing-profile-id"
    assert profiles.lookups == ["existing-profile-id"]
    assert mappings.lookups == []


def test_cognito_token_resolves_through_mapping_not_claimed_subject(monkeypatch):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = jwt.encode(
        {"sub": "cognito-subject", "exp": 4102444800},
        private_key,
        algorithm="RS256",
    )
    monkeypatch.setattr(
        identity_resolver,
        "decode_cognito_access_token",
        lambda value: {"sub": "cognito-subject", "role": "MANAGEMENT"},
    )
    profiles = FakeProfileRepository({"existing-profile-id": _profile("existing-profile-id", "EMPLOYEE")})
    mappings = FakeCognitoMappingRepository({"cognito-subject": "existing-profile-id"})

    resolved = identity_resolver.resolve_profile_from_bearer_token(token, profiles, mappings)

    assert resolved.id == "existing-profile-id"
    assert resolved.role == "EMPLOYEE"
    assert profiles.lookups == ["existing-profile-id"]
    assert mappings.lookups == ["cognito-subject"]


def test_unmapped_cognito_subject_has_no_profile(monkeypatch):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = jwt.encode({"sub": "unknown-sub"}, private_key, algorithm="RS256")
    monkeypatch.setattr(
        identity_resolver,
        "decode_cognito_access_token",
        lambda value: {"sub": "unknown-sub"},
    )
    profiles = FakeProfileRepository({})
    mappings = FakeCognitoMappingRepository({})

    assert identity_resolver.resolve_profile_from_bearer_token(token, profiles, mappings) is None
    assert profiles.lookups == []


def test_inactive_cognito_mapped_profile_is_rejected(monkeypatch):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = jwt.encode({"sub": "cognito-sub"}, private_key, algorithm="RS256")
    monkeypatch.setattr(
        identity_resolver,
        "decode_cognito_access_token",
        lambda value: {"sub": "cognito-sub"},
    )
    profiles = FakeProfileRepository({"profile-id": _profile("profile-id", active=False)})
    mappings = FakeCognitoMappingRepository({"cognito-sub": "profile-id"})

    assert identity_resolver.resolve_profile_from_bearer_token(token, profiles, mappings) is None


def test_rejects_unknown_token_algorithm():
    token = jwt.encode({"sub": "attacker"}, key="", algorithm="none")
    with pytest.raises(AuthenticationError, match="Unsupported authentication token algorithm"):
        identity_resolver.resolve_profile_from_bearer_token(
            token,
            FakeProfileRepository({}),
            FakeCognitoMappingRepository({}),
        )
