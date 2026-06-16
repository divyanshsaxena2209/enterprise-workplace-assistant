"""
ProfileService — business logic for profile read and update operations.

Rules:
- Delegates all DB access to ProfileRepository.
- Returns ProfileResponse schemas (API-facing), not raw models.
- Raises domain exceptions from app/core/exceptions.py.
"""

from supabase import Client

from app.core.exceptions import NotFoundError, ValidationError
from app.repositories.profile_repository import ProfileRepository
from app.schemas.profile import ProfileResponse, ProfileUpdateRequest


class ProfileService:
    """Handles profile retrieval and updates."""

    def __init__(self, client: Client) -> None:
        self._repo = ProfileRepository(client)

    def get_profile(self, user_id: str) -> ProfileResponse:
        """
        Retrieve a user's full profile.

        Args:
            user_id: UUID string of the authenticated user.

        Returns:
            ProfileResponse with all profile fields.

        Raises:
            NotFoundError: if no profile exists for the given user_id.
        """
        profile = self._repo.get_by_id_or_raise(user_id)

        if not profile.is_active:
            raise NotFoundError("This account has been deactivated. Please contact support.")

        return ProfileResponse.from_model(profile)

    def update_profile(
        self, user_id: str, updates: ProfileUpdateRequest
    ) -> ProfileResponse:
        """
        Apply partial updates to a user's profile.

        Args:
            user_id: UUID string of the authenticated user.
            updates: Validated ProfileUpdateRequest — only set fields are applied.

        Returns:
            Updated ProfileResponse.

        Raises:
            NotFoundError: if the profile doesn't exist.
            ValidationError: if the update dict is empty after filtering.
        """
        update_dict = updates.to_update_dict()

        if not update_dict:
            raise ValidationError(
                "No updateable fields were provided in the request body."
            )

        updated = self._repo.update(user_id, update_dict)
        return ProfileResponse.from_model(updated)
