"""
Recruiter Note Repository
Handles database operations for recruiter notes.
"""

from typing import List, Dict, Any
from uuid import UUID
from supabase import Client

from app.core.exceptions import DatabaseError, NotFoundError
from app.schemas.recruiter_notes import RecruiterNoteResponse

class RecruiterNoteRepository:
    def __init__(self, client: Client) -> None:
        self._db = client

    def create_note(self, note_data: Dict[str, Any]) -> RecruiterNoteResponse:
        try:
            res = self._db.table("recruiter_notes").insert(note_data).execute()
            if not res.data:
                raise DatabaseError("Failed to insert recruiter note.")
            return RecruiterNoteResponse.model_validate(res.data[0])
        except Exception as exc:
            raise DatabaseError(f"Failed to create note: {exc}") from exc

    def get_notes_by_application(self, application_id: str | UUID) -> List[RecruiterNoteResponse]:
        try:
            res = self._db.table("recruiter_notes").select("*").eq("application_id", str(application_id)).order("created_at", desc=True).execute()
            return [RecruiterNoteResponse.model_validate(row) for row in res.data]
        except Exception as exc:
            raise DatabaseError(f"Failed to fetch recruiter notes: {exc}") from exc

    def get_note_by_id(self, note_id: str | UUID) -> RecruiterNoteResponse:
        try:
            res = self._db.table("recruiter_notes").select("*").eq("id", str(note_id)).execute()
            if not res.data:
                raise NotFoundError(f"Recruiter note '{note_id}' not found.")
            return RecruiterNoteResponse.model_validate(res.data[0])
        except NotFoundError:
            raise
        except Exception as exc:
            raise DatabaseError(f"Failed to fetch note: {exc}") from exc

    def update_note(self, note_id: str | UUID, update_data: Dict[str, Any]) -> RecruiterNoteResponse:
        try:
            res = self._db.table("recruiter_notes").update(update_data).eq("id", str(note_id)).execute()
            if not res.data:
                raise NotFoundError(f"Recruiter note '{note_id}' not found or deleted.")
            return RecruiterNoteResponse.model_validate(res.data[0])
        except NotFoundError:
            raise
        except Exception as exc:
            raise DatabaseError(f"Failed to update note: {exc}") from exc

    def delete_note(self, note_id: str | UUID) -> None:
        try:
            res = self._db.table("recruiter_notes").delete().eq("id", str(note_id)).execute()
            if not res.data:
                raise NotFoundError(f"Recruiter note '{note_id}' not found.")
        except NotFoundError:
            raise
        except Exception as exc:
            raise DatabaseError(f"Failed to delete note: {exc}") from exc
