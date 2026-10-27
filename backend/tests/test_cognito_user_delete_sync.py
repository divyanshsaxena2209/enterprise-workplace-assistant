from app.lambdas import cognito_user_delete_sync as sync


POOL_ID = "ap-south-1_89s6YRnwQ"


def _event(request_parameters=None, additional=None, event_name="AdminDeleteUser"):
    return {
        "source": "aws.cognito-idp",
        "detail-type": "AWS API Call via CloudTrail",
        "region": "ap-south-1",
        "detail": {
            "eventSource": "cognito-idp.amazonaws.com",
            "eventName": event_name,
            "requestParameters": request_parameters or {"userPoolId": POOL_ID},
            "additionalEventData": additional or {},
        },
    }


def test_admin_delete_user_removes_only_the_linked_supabase_auth_identity(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://staging.example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-only-key")
    monkeypatch.setenv("COGNITO_USER_POOL_ID", POOL_ID)
    calls = []

    def fake_request(method, path, params=None):
        calls.append((method, path, params))
        if path == "rest/v1/cognito_identity_mappings" and params and "cognito_sub" in params:
            return 200, [{"profile_id": "auth-profile-id"}]
        if path == "auth/v1/admin/users/auth-profile-id":
            return 200, None
        if path == "rest/v1/profiles":
            return 200, []
        if path == "rest/v1/cognito_identity_mappings":
            return 200, []
        raise AssertionError(f"Unexpected Supabase request: {method} {path} {params}")

    monkeypatch.setattr(sync, "_supabase_request", fake_request)
    event = _event(
        {"userPoolId": POOL_ID, "username": "employee"},
        {"UserSub": "deleted-cognito-sub"},
    )

    result = sync.handler(event, None)

    assert result == {"status": "deleted", "matched_by": "subject"}
    assert ("DELETE", "auth/v1/admin/users/auth-profile-id", None) in calls


def test_username_fallback_is_scoped_to_the_configured_pool(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://staging.example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-only-key")
    monkeypatch.setenv("COGNITO_USER_POOL_ID", POOL_ID)
    calls = []

    def fake_request(method, path, params=None):
        calls.append((method, path, params))
        if path == "rest/v1/cognito_identity_mappings" and params and "cognito_username" in params:
            assert params["cognito_user_pool_id"] == f"eq.{POOL_ID}"
            if "ilike" in params["cognito_username"]:
                return 200, [{
                    "profile_id": "auth-profile-id",
                    "cognito_last_verified_at": "2026-10-27T10:00:00+00:00",
                }]
            return 200, []
        if path == "auth/v1/admin/users/auth-profile-id":
            return 200, None
        if path in {"rest/v1/profiles", "rest/v1/cognito_identity_mappings"}:
            return 200, []
        raise AssertionError(f"Unexpected Supabase request: {method} {path} {params}")

    monkeypatch.setattr(sync, "_supabase_request", fake_request)
    event = _event({"userPoolId": POOL_ID, "username": "employee@example.test"})
    event["time"] = "2026-10-27T11:00:00Z"

    result = sync.handler(event, None)

    assert result == {"status": "deleted", "matched_by": "username"}
    assert any(method == "DELETE" for method, _, _ in calls)


def test_delete_from_a_different_pool_does_not_touch_supabase(monkeypatch):
    monkeypatch.setenv("COGNITO_USER_POOL_ID", POOL_ID)
    monkeypatch.setattr(sync, "_supabase_request", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("must not call Supabase")))
    event = _event({"userPoolId": "ap-south-1_otherPool", "username": "employee"})

    assert sync.handler(event, None) == {"status": "ignored", "reason": "different-user-pool"}


def test_unknown_user_event_does_not_delete_any_supabase_account(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://staging.example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-only-key")
    monkeypatch.setenv("COGNITO_USER_POOL_ID", POOL_ID)
    monkeypatch.setattr(sync, "_supabase_request", lambda *_args, **_kwargs: (200, []))

    assert sync.handler(
        _event({"userPoolId": POOL_ID, "username": "unmapped"}, {"UserSub": "unmapped-sub"}),
        None,
    ) == {"status": "no-linked-identity", "reason": "subject-not-mapped"}


def test_stale_username_only_delete_event_cannot_remove_newer_mapping(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://staging.example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-only-key")
    monkeypatch.setenv("COGNITO_USER_POOL_ID", POOL_ID)
    calls = []

    def fake_request(method, path, params=None):
        calls.append((method, path, params))
        if path == "rest/v1/cognito_identity_mappings" and params and "cognito_username" in params:
            return 200, [{
                "profile_id": "new-auth-user-id",
                "cognito_last_verified_at": "2026-10-27T11:05:00+00:00",
            }]
        raise AssertionError("A stale delete must not reach Auth deletion or verification.")

    monkeypatch.setattr(sync, "_supabase_request", fake_request)
    event = _event({"userPoolId": POOL_ID, "username": "same@example.test"})
    event["time"] = "2026-10-27T11:00:00Z"

    result = sync.handler(event, None)

    assert result == {"status": "no-linked-identity", "reason": "stale-delete-event"}
    assert not any(method == "DELETE" for method, _, _ in calls)
