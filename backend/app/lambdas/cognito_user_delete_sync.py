"""Keep staging Supabase identities synchronized with the Cognito staging pool.

CloudTrail/EventBridge handles deletes promptly. A scheduled reconciliation is a
backstop for best-effort CloudTrail delivery. Only profile mappings for the
configured user pool are considered; job rows survive because jobs.created_by
uses ON DELETE SET NULL.
"""
from __future__ import annotations

import boto3
import json
import logging
import os
import re
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen

logger = logging.getLogger()
logger.setLevel(logging.INFO)
_ALLOWED_DELETE_EVENTS = {"DeleteUser", "AdminDeleteUser"}
_PAGE_SIZE = 1000


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


def _parse_time(value: str | None):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _find_mapping(subject: str | None, username: str | None, pool_id: str, event_time: str | None):
    pool_filter = {"cognito_user_pool_id": f"eq.{pool_id}"}
    if subject:
        # If CloudTrail gives a subject, never fall back to username on mismatch.
        # This prevents a delayed delete for an older user from removing a newer
        # Cognito account that has reused the same username/email.
        status, data = _supabase_request(
            "GET", "rest/v1/cognito_identity_mappings",
            {
                "select": "profile_id,cognito_last_verified_at",
                "cognito_sub": f"eq.{subject}",
                **pool_filter,
                "limit": "1",
            },
        )
        if status == 200 and data:
            return str(data[0]["profile_id"]), "subject", None
        return None, None, "subject-not-mapped"

    if username and re.fullmatch(r"[A-Za-z0-9@._+\\-]{1,128}", username):
        event_time_parsed = _parse_time(event_time)
        if event_time_parsed is None:
            raise ValueError("CloudTrail deletion event had no valid timestamp; refusing unsafe username-only cleanup.")
        for operator in ("eq", "ilike"):
            status, data = _supabase_request(
                "GET", "rest/v1/cognito_identity_mappings",
                {
                    "select": "profile_id,cognito_last_verified_at",
                    "cognito_username": f"{operator}.{username}",
                    **pool_filter,
                    "limit": "1",
                },
            )
            if status != 200 or not data:
                continue
            last_verified = _parse_time(data[0].get("cognito_last_verified_at"))
            if last_verified is None:
                raise RuntimeError("Mapping lacks its last-verified timestamp; refusing username-only cleanup.")
            if last_verified >= event_time_parsed:
                return None, None, "stale-delete-event"
            return str(data[0]["profile_id"]), "username", None
    return None, None, "no-linked-identity"


def _list_staging_mappings(pool_id: str):
    rows = []
    offset = 0
    while True:
        status, data = _supabase_request(
            "GET",
            "rest/v1/cognito_identity_mappings",
            {
                "select": "profile_id,cognito_sub",
                "cognito_user_pool_id": f"eq.{pool_id}",
                "limit": str(_PAGE_SIZE),
                "offset": str(offset),
            },
        )
        if status != 200 or not isinstance(data, list):
            raise RuntimeError("Could not list staging Cognito identity mappings for reconciliation.")
        rows.extend(data)
        if len(data) < _PAGE_SIZE:
            return rows
        offset += len(data)


def _delete_mapped_supabase_identity(profile_id: str):
    # Supabase Auth deletion cascades public.profiles and its mapping. Existing
    # job rows remain because jobs.created_by uses ON DELETE SET NULL.
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


def _reconcile_deleted_cognito_users():
    pool_id = os.environ["COGNITO_USER_POOL_ID"]
    # Fetch the complete Cognito user list before deleting anything; any AWS
    # pagination/API error aborts the run and lets EventBridge retry it.
    client = boto3.client("cognito-idp", region_name=os.getenv("AWS_REGION", "ap-south-1"))
    paginator = client.get_paginator("list_users")
    live_subjects = set()
    for page in paginator.paginate(UserPoolId=pool_id):
        for user in page.get("Users", []):
            attrs = {
                item.get("Name"): item.get("Value")
                for item in user.get("Attributes", [])
                if isinstance(item, dict)
            }
            if attrs.get("sub"):
                live_subjects.add(attrs["sub"])

    mappings = _list_staging_mappings(pool_id)
    stale = [
        row for row in mappings
        if row.get("cognito_sub") and row["cognito_sub"] not in live_subjects
    ]
    deleted = 0
    for row in stale:
        _delete_mapped_supabase_identity(str(row["profile_id"]))
        deleted += 1

    logger.info(
        "Cognito/Supabase reconciliation completed for configured pool; mappings=%d stale_removed=%d",
        len(mappings), deleted,
    )
    return {"status": "reconciled", "mappings_checked": len(mappings), "identities_removed": deleted}


def handler(event, context):
    # EventBridge scheduled reconciliation is the safety net in case CloudTrail
    # delivers no delete event or the event cannot be correlated automatically.
    if event.get("source") == "aws.events" and event.get("detail-type") == "Scheduled Event":
        return _reconcile_deleted_cognito_users()

    detail = event.get("detail") or event
    event_name = detail.get("eventName") or detail.get("event_name")
    if detail.get("errorCode") or detail.get("errorMessage"):
        logger.info("Ignoring unsuccessful Cognito delete API event.")
        return {"status": "ignored", "reason": "delete-api-call-failed"}
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

    event_time = event.get("time") or detail.get("eventTime") or detail.get("event_time")
    profile_id, matched_by, no_match_reason = _find_mapping(subject, username, expected_pool, event_time)
    if not profile_id:
        logger.info("No staging Supabase identity deleted for Cognito event; reason=%s", no_match_reason)
        return {"status": "no-linked-identity", "reason": no_match_reason}

    _delete_mapped_supabase_identity(profile_id)
    logger.info("Cognito deletion cleanup verified for linked Supabase identity; match=%s", matched_by)
    return {"status": "deleted", "matched_by": matched_by}
