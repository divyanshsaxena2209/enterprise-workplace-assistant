"""
Recruiter Note Service
Handles business logic and authorization for recruiter notes.
"""

from typing import List, Dict, Any
from uuid import UUID
from supabase import Client

from app.core.exceptions import AuthorizationError
from app.schemas.recruiter_notes import RecruiterNoteResponse, RecruiterNoteCreate, RecruiterNoteUpdate
from app.repositories.recruiter_note_repository import RecruiterNoteRepository

class RecruiterNoteService:
    def __init__(self, client: Client):
        self.repo = RecruiterNoteRepository(client)

    def add_note(self, application_id: str | UUID, note_data: RecruiterNoteCreate, author_id: str | UUID) -> RecruiterNoteResponse:
        data = {
            "application_id": str(application_id),
            "author_id": str(author_id),
            "note": note_data.note
        }
        return self.repo.create_note(data)

    def get_notes(self, application_id: str | UUID) -> List[RecruiterNoteResponse]:
        return self.repo.get_notes_by_application(application_id)

    def update_note(self, note_id: str | UUID, note_data: RecruiterNoteUpdate, current_user: dict) -> RecruiterNoteResponse:
        # Fetch existing to verify authorization
        existing = self.repo.get_note_by_id(note_id)
        
        # Only the author or Management can edit
        is_author = str(existing.author_id) == str(current_user["id"])
        is_management = current_user.get("role") == "MANAGEMENT"
        
        if not (is_author or is_management):
            raise AuthorizationError("You can only edit your own notes.")
            
        update_dict = {"note": note_data.note}
        return self.repo.update_note(note_id, update_dict)

    def delete_note(self, note_id: str | UUID, current_user: dict) -> None:
        existing = self.repo.get_note_by_id(note_id)
        
        is_author = str(existing.author_id) == str(current_user["id"])
        is_management = current_user.get("role") == "MANAGEMENT"
        
        if not (is_author or is_management):
            raise AuthorizationError("You can only delete your own notes.")
            
        self.repo.delete_note(note_id)
