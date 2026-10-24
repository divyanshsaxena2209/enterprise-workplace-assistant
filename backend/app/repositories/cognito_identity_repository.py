"""Trusted mapping between Cognito subjects and existing Supabase profiles.

All access uses the backend's service-role client. The migration deliberately
provides no browser-client policies for this table.
"""
from supabase import Client

from app.core.exceptions import ConflictError, DatabaseError


_TABLE = "cognito_identity_mappings"


class CognitoIdentityRepository:
    def __init__(self, client: Client) -> None:
        self._db = client

    def get_profile_id(self, cognito_sub: str) -> str | None:
        try:
            response = (
                self._db.table(_TABLE)
                .select("profile_id")
                .eq("cognito_sub", cognito_sub)
                .limit(1)
                .execute()
            )
        except Exception as exc:
            raise DatabaseError(
                "Cognito identity mapping is unavailable. Apply the staging mapping migration first."
            ) from exc
        if not response.data:
            return None
        return str(response.data[0]["profile_id"])

    def get_subject_for_profile(self, profile_id: str) -> str | None:
        try:
            response = (
                self._db.table(_TABLE)
                .select("cognito_sub")
                .eq("profile_id", profile_id)
                .limit(1)
                .execute()
            )
        except Exception as exc:
            raise DatabaseError(
                "Cognito identity mapping is unavailable. Apply the staging mapping migration first."
            ) from exc
        if not response.data:
            return None
        return str(response.data[0]["cognito_sub"])

    def create_mapping(self, cognito_sub: str, profile_id: str) -> None:
        existing_profile_id = self.get_profile_id(cognito_sub)
        if existing_profile_id is not None:
            if existing_profile_id == profile_id:
                return
            raise ConflictError("This Cognito identity is already linked to another profile.")

        existing_subject = self.get_subject_for_profile(profile_id)
        if existing_subject is not None:
            if existing_subject == cognito_sub:
                return
            raise ConflictError("This profile is already linked to a different Cognito identity.")

        try:
            self._db.table(_TABLE).insert(
                {"cognito_sub": cognito_sub, "profile_id": profile_id}
            ).execute()
        except Exception as exc:
            # A concurrent link may have won the unique constraint race. Never
            # silently reassign a mapping; only accept an exact existing match.
            existing_profile_id = self.get_profile_id(cognito_sub)
            if existing_profile_id == profile_id:
                return
            raise ConflictError(
                "Could not link this Cognito identity; it may already be linked."
            ) from exc
