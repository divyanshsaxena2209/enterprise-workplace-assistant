"""
ProfileRepository — all database access for the profiles table.

Rules:
- NO raw SQL. All queries use the Supabase Python client.
- NO HTTPException. Raise domain exceptions from app/core/exceptions.py.
- All methods return ProfileModel or None — never raw dicts outside this class.
"""

from typing import Optional

from supabase import Client

from app.core.exceptions import ConflictError, DatabaseError, NotFoundError
from app.models.profile import ProfileModel

_TABLE = "profiles"


class ProfileRepository:
    """Data access object for the public.profiles table."""

    def __init__(self, client: Client) -> None:
        self._db = client

    # -------------------------------------------------------------------------
    # Read
    # -------------------------------------------------------------------------

    def get_by_id(self, user_id: str) -> Optional[ProfileModel]:
        """
        Fetch a profile by its UUID (== auth.users.id).
        Returns None if not found.
        Raises DatabaseError on unexpected failures.
        """
        try:
            response = (
                self._db.table(_TABLE)
                .select("*")
                .eq("id", user_id)
                .limit(1)
                .execute()
            )
        except Exception as exc:
            raise DatabaseError(f"Failed to fetch profile by ID: {exc}") from exc

        if not response.data:
            return None
        return ProfileModel.from_dict(response.data[0])

    def get_by_id_or_raise(self, user_id: str) -> ProfileModel:
        """Like get_by_id but raises NotFoundError instead of returning None."""
        profile = self.get_by_id(user_id)
        if profile is None:
            raise NotFoundError(f"Profile with ID '{user_id}' was not found.")
        return profile

    def get_by_email(self, email: str) -> Optional[ProfileModel]:
        """
        Fetch a profile by email address.
        Returns None if not found.
        """
        try:
            response = (
                self._db.table(_TABLE)
                .select("*")
                .eq("email", email.lower().strip())
                .limit(1)
                .execute()
            )
        except Exception as exc:
            raise DatabaseError(f"Failed to fetch profile by email: {exc}") from exc

        if not response.data:
            return None
        return ProfileModel.from_dict(response.data[0])

    # -------------------------------------------------------------------------
    # Write
    # -------------------------------------------------------------------------

    def create(self, profile_data: dict) -> ProfileModel:
        """
        Insert a new profile row.
        Raises ConflictError if email already exists.
        Raises DatabaseError on other failures.
        """
        try:
            response = self._db.table(_TABLE).insert(profile_data).execute()
        except Exception as exc:
            exc_str = str(exc).lower()
            if "unique" in exc_str or "duplicate" in exc_str or "23505" in exc_str:
                raise ConflictError(
                    "A profile with this email address already exists."
                ) from exc
            raise DatabaseError(f"Failed to create profile: {exc}") from exc

        if not response.data:
            raise DatabaseError("Profile insert returned no data.")
        return ProfileModel.from_dict(response.data[0])

    def upsert(self, profile_data: dict) -> ProfileModel:
        """
        Insert or update a profile row (by primary key `id`).
        Used during signup to handle cases where the DB trigger already
        created a partial profile from raw_user_meta_data.
        """
        try:
            response = (
                self._db.table(_TABLE)
                .upsert(profile_data, on_conflict="id")
                .execute()
            )
        except Exception as exc:
            raise DatabaseError(f"Failed to upsert profile: {exc}") from exc

        if not response.data:
            raise DatabaseError("Profile upsert returned no data.")
        return ProfileModel.from_dict(response.data[0])

    def update(self, user_id: str, updates: dict) -> ProfileModel:
        """
        Partially update a profile.
        Only keys present in `updates` are changed.
        Raises NotFoundError if no row matches.
        Raises DatabaseError on failures.
        """
        if not updates:
            # Nothing to update — return current state.
            return self.get_by_id_or_raise(user_id)

        try:
            response = (
                self._db.table(_TABLE)
                .update(updates)
                .eq("id", user_id)
                .execute()
            )
        except Exception as exc:
            raise DatabaseError(f"Failed to update profile: {exc}") from exc

        if not response.data:
            raise NotFoundError(f"Profile with ID '{user_id}' was not found.")
        return ProfileModel.from_dict(response.data[0])
