"""EventBridge handler that mirrors Cognito deletes into staging Supabase Auth.

Acts only on the configured Cognito pool and only when the subject or username
matches that pool's identity mapping. Deleting auth.users cascades the profile
and mapping; jobs and application history are retained by existing FK actions.
"""
from __future__ import annotations

import json
import logging
import os
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen

logger = logging.getLogger()
logger.setLevel(logging.INFO)
_ALLOWED_DELETE_EVENTS = {"AdminDeleteUser", "DeleteUser"}


def _first_value(*values):
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _pool_id_from_event(event, detail, request, additional):
    value = _first_value(
        request.get("userPoolId"), request.get("UserPoolId"),
        additional.get("userPoolId"), additional.get("UserPoolId"),
        detail.get("userPoolId"), detail.get("UserPoolId"),
    )
    if value:
        return value
    resources = event.get("resources") or detail.get("resources") or []
    for resource in resources:
        if isinstance(resource, str) and ":userpool/" in resource:
            return resource.rsplit(":userpool/", 1)[1]
        if isinstance(resource, dict):
            arn = resource.get("ARN") or resource.get("arn")
            if isinstance(arn, str) and ":userpool/" in arn:
                return arn.rsplit(":userpool/", 1)[1]
    return None


def _identity_from_event(detail, request, additional):
    subject = _first_value(
        request.get("userSub"), request.get("UserSub"), request.get("sub"),
        additional.get("userSub"), additional.get("UserSub"), additional.get("sub"),
        detail.get("userSub"), detail.get("UserSub"), detail.get("sub"),
    )
    username = _first_value(
        request.get("username"), request.get("Username"),
        request.get("userName"), request.get("UserName"),
        additional.get("username"), additional.get("Username"),
        detail.get("username"), detail.get("Username"),
    )
    nested = additional.get("requestParameters")
    if isinstance(nested, dict):
        username = username or _first_value(
            nested.get("username"), nested.get("Username"),
            nested.get("userName"), nested.get("UserName"),
        )
        subject = subject or _first_value(
            nested.get("userSub"), nested.get("UserSub"), nested.get("sub")
        )
    return subject, username


def _supabase_request(method: str, path: str, params: dict | None = None):
    base_url = os.environ["SUPABASE_URL"].rstrip("/")
    service_key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    url = f"{base_url}/{path.lstrip('/')}"
    if params:
        url += "?" + urlencode(params)
    request = Request(
        url,
        method=method,
        headers={
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=10) as response:
            body = response.read()
            return response.status, json.loads(body.decode("utf-8")) if body else None
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        if method == "DELETE" and exc.code == 404:
            return 404, body
        raise RuntimeError(f"Supabase request failed: HTTP {exc.code}") from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError("Could not reach staging Supabase for Cognito deletion cleanup.") from exc


def _find_mapping(subject: str | None, username: str | None, pool_id: str):
    pool_filter = {"cognito_user_pool_id": f"eq.{pool_id}"}
    if subject:
        status, data = _supabase_request(
            "GET", "rest/v1/cognito_identity_mappings",
            {"select": "profile_id", "cognito_sub": f"eq.{subject}", **pool_filter, "limit": "1"},
        )
        if status == 200 and data:
            return str(data[0]["profile_id"]), "subject"
    if username and re.fullmatch(r"[A-Za-z0-9@._+\\-]{1,128}", username):
        status, data = _supabase_request(
            "GET", "rest/v1/cognito_identity_mappings",
            {"select": "profile_id", "cognito_username": f"eq.{username}", **pool_filter, "limit": "1"},
        )
        if status == 200 and data:
            return str(data[0]["profile_id"]), "username"
        status, data = _supabase_request(
            "GET", "rest/v1/cognito_identity_mappings",
            {"select": "profile_id", "cognito_username": f"ilike.{username}", **pool_filter, "limit": "1"},
        )
        if status == 200 and data:
            return str(data[0]["profile_id"]), "username"
    return None, None


def handler(event, context):
    detail = event.get("detail") or event
    event_name = detail.get("eventName") or detail.get("event_name")
    if event_name not in _ALLOWED_DELETE_EVENTS:
        logger.info("Ignoring non-delete Cognito event: %s", event_name)
        return {"status": "ignored", "reason": "not-a-user-delete"}

    expected_pool = os.environ["COGNITO_USER_POOL_ID"]
    request = detail.get("requestParameters") or detail.get("request_parameters") or {}
    additional = detail.get("additionalEventData") or detail.get("additional_event_data") or {}
    pool_id = _pool_id_from_event(event, detail, request, additional)
    if pool_id and pool_id != expected_pool:
        logger.info("Ignoring delete from a different Cognito user pool.")
        return {"status": "ignored", "reason": "different-user-pool"}

    subject, username = _identity_from_event(detail, request, additional)
    if not subject and not username:
        logger.error("Cognito deletion event had no subject or username; no account will be deleted.")
        raise ValueError("Cognito deletion event has no correlatable user identity.")

    profile_id, matched_by = _find_mapping(subject, username, expected_pool)
    if not profile_id:
        logger.info("No linked staging Supabase identity matched the Cognito deletion event.")
        return {"status": "no-linked-identity"}

    # The Auth admin delete cascades public.profiles and its Cognito mapping. Jobs
    # remain intact because jobs.created_by is ON DELETE SET NULL.
    status, _ = _supabase_request(
        "DELETE", f"auth/v1/admin/users/{quote(profile_id, safe='')}",
    )
    if status not in (200, 204, 404):
        raise RuntimeError(f"Supabase Auth deletion returned unexpected HTTP {status}")

    status, profile_rows = _supabase_request(
        "GET", "rest/v1/profiles",
        {"select": "id", "id": f"eq.{profile_id}", "limit": "1"},
    )
    if status != 200 or profile_rows:
        raise RuntimeError("Supabase profile still exists after Auth user deletion.")
    status, mapping_rows = _supabase_request(
        "GET", "rest/v1/cognito_identity_mappings",
        {"select": "profile_id", "profile_id": f"eq.{profile_id}", "limit": "1"},
    )
    if status != 200 or mapping_rows:
        raise RuntimeError("Cognito mapping still exists after Auth user deletion.")

    logger.info("Cognito deletion cleanup verified for linked Supabase identity; match=%s", matched_by)
    return {"status": "deleted", "matched_by": matched_by}
