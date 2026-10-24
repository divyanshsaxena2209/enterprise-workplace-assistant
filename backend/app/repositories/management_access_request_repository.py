"""Repository for the server-only Management access request workflow."""

from datetime import datetime, timezone
from typing import Any

from supabase import Client

from app.core.exceptions import (
    AuthorizationError,
    ConflictError,
    DatabaseError,
    NotFoundError,
)

_TABLE = "management_access_requests"


class ManagementAccessRequestRepository:
    """Read/write request records through the backend's service-role client only."""

    def __init__(self, client: Client) -> None:
        self._db = client

    def get_for_profile(self, profile_id: str) -> dict[str, Any] | None:
        try:
            response = (
                self._db.table(_TABLE)
                .select("profile_id,requested_role,status,request_note,reviewer_id,reviewer_note,requested_at,reviewed_at,updated_at")
                .eq("profile_id", profile_id)
                .limit(1)
                .execute()
            )
        except Exception as exc:
            raise DatabaseError("Could not read the Management access request.") from exc
        return response.data[0] if response.data else None

    def list_pending(self) -> list[dict[str, Any]]:
        try:
            response = (
                self._db.table(_TABLE)
                .select("profile_id,requested_role,status,request_note,requested_at")
                .eq("status", "PENDING")
                .order("requested_at", desc=False)
                .execute()
            )
        except Exception as exc:
            raise DatabaseError("Could not list pending Management access requests.") from exc
        return list(response.data or [])

    def submit(self, profile_id: str, request_note: str | None = None) -> dict[str, Any]:
        """Idempotently submit a request; only a Management reviewer can approve it."""
        existing = self.get_for_profile(profile_id)
        if existing:
            if existing["status"] != "REJECTED":
                return existing
            try:
                response = (
                    self._db.table(_TABLE)
                    .update({
                        "status": "PENDING",
                        "request_note": request_note,
                        "reviewer_id": None,
                        "reviewer_note": None,
                        "reviewed_at": None,
                        "requested_at": datetime.now(timezone.utc).isoformat(),
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    })
                    .eq("profile_id", profile_id)
                    .eq("status", "REJECTED")
                    .execute()
                )
                if response.data:
                    return response.data[0]
            except Exception as exc:
                raise DatabaseError("Could not resubmit the Management access request.") from exc
            # A concurrent reviewer may have updated it between read and write.
            latest = self.get_for_profile(profile_id)
            if latest:
                return latest
            raise ConflictError("The Management access request changed concurrently.")

        payload = {
            "profile_id": profile_id,
            "requested_role": "MANAGEMENT",
            "status": "PENDING",
            "request_note": request_note,
        }
        try:
            response = self._db.table(_TABLE).insert(payload).execute()
            if response.data:
                return response.data[0]
        except Exception as exc:
            # Unique profile_id makes callback retries idempotent. Re-read after a
            # uniqueness race, but never reassign roles or overwrite approval data.
            latest = self.get_for_profile(profile_id)
            if latest:
                return latest
            raise DatabaseError("Could not submit the Management access request.") from exc
        raise DatabaseError("Management access request insert returned no record.")

    def mark_allowlisted_approved(self, profile_id: str) -> dict[str, Any]:
        """Record Management access granted by trusted server-side allowlist configuration."""
        now = datetime.now(timezone.utc).isoformat()
        existing = self.get_for_profile(profile_id)
        if existing and existing.get("status") == "APPROVED":
            return existing

        payload = {
            "requested_role": "MANAGEMENT",
            "status": "APPROVED",
            "reviewer_id": None,
            "reviewer_note": "Granted through the configured trusted Management email allowlist.",
            "reviewed_at": now,
            "updated_at": now,
        }
        try:
            if existing:
                response = (
                    self._db.table(_TABLE)
                    .update(payload)
                    .eq("profile_id", profile_id)
                    .execute()
                )
                if response.data:
                    return response.data[0]
                latest = self.get_for_profile(profile_id)
                if latest:
                    return latest
                raise ConflictError("The Management access record changed concurrently.")

            payload["profile_id"] = profile_id
            payload["request_note"] = None
            payload["requested_at"] = now
            response = self._db.table(_TABLE).insert(payload).execute()
            if response.data:
                return response.data[0]
        except ConflictError:
            raise
        except Exception as exc:
            latest = self.get_for_profile(profile_id)
            if latest and latest.get("status") == "APPROVED":
                return latest
            raise DatabaseError("Could not record allowlisted Management access.") from exc
        latest = self.get_for_profile(profile_id)
        if latest:
            return latest
        raise DatabaseError("Allowlisted Management access record returned no data.")

    def review(
        self,
        *,
        profile_id: str,
        decision: str,
        reviewer_id: str,
        reviewer_note: str | None = None,
    ) -> str:
        normalized_decision = decision.strip().upper()
        if normalized_decision not in {"APPROVE", "REJECT"}:
            raise ConflictError("Decision must be APPROVE or REJECT.")

        try:
            response = self._db.rpc(
                "review_management_access_request",
                {
                    "p_profile_id": profile_id,
                    "p_decision": normalized_decision,
                    "p_reviewer_id": reviewer_id,
                    "p_reviewer_note": reviewer_note,
                },
            ).execute()
            value = response.data
            if isinstance(value, str) and value in {"APPROVED", "REJECTED"}:
                return value
            if isinstance(value, list) and value and value[0] in {"APPROVED", "REJECTED"}:
                return value[0]
            raise DatabaseError("The Management access review returned an unexpected result.")
        except DatabaseError:
            raise
        except Exception as exc:
            message = str(exc).lower()
            if "management profile is required" in message:
                raise AuthorizationError("An active Management account is required to approve requests.") from exc
            if "request not found" in message:
                raise NotFoundError("Management access request not found.") from exc
            if "only pending" in message or "only active employee" in message:
                raise ConflictError("This request is no longer eligible for review.") from exc
            raise DatabaseError("Could not complete the Management access review.") from exc
