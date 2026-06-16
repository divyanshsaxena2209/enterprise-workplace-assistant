from fastapi import APIRouter, Depends, status
from typing import List
from uuid import UUID
from supabase import Client

from app.db.supabase import get_supabase_client
from app.dependencies.auth import require_management
from app.schemas.profile import ProfileResponse
from app.schemas.recruiter_notes import RecruiterNoteCreate, RecruiterNoteUpdate, RecruiterNoteResponse
from app.services.recruiter_note_service import RecruiterNoteService

router = APIRouter(tags=["Recruiter Notes"])

def get_note_service(client: Client = Depends(get_supabase_client)) -> RecruiterNoteService:
    return RecruiterNoteService(client)

@router.post(
    "/applications/{application_id}/notes",
    response_model=RecruiterNoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Recruiter Note",
    description="Adds a new note to an application. Management only."
)
def add_note(
    application_id: UUID,
    note: RecruiterNoteCreate,
    current_user: ProfileResponse = Depends(require_management),
    service: RecruiterNoteService = Depends(get_note_service)
):
    return service.add_note(application_id, note, current_user.id)

@router.get(
    "/applications/{application_id}/notes",
    response_model=List[RecruiterNoteResponse],
    summary="List Recruiter Notes",
    description="Lists all notes for a given application. Management only."
)
def get_notes(
    application_id: UUID,
    current_user: ProfileResponse = Depends(require_management),
    service: RecruiterNoteService = Depends(get_note_service)
):
    return service.get_notes(application_id)

@router.patch(
    "/notes/{note_id}",
    response_model=RecruiterNoteResponse,
    summary="Update Recruiter Note",
    description="Updates a recruiter note. Only the author or Management can perform this action."
)
def update_note(
    note_id: UUID,
    note: RecruiterNoteUpdate,
    current_user: ProfileResponse = Depends(require_management),
    service: RecruiterNoteService = Depends(get_note_service)
):
    # Pass current_user dict logic. Our model is ProfileResponse which acts as a dict via model_dump()
    return service.update_note(note_id, note, current_user.model_dump())

@router.delete(
    "/notes/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Recruiter Note",
    description="Soft deletes a recruiter note. Only the author or Management can perform this action."
)
def delete_note(
    note_id: UUID,
    current_user: ProfileResponse = Depends(require_management),
    service: RecruiterNoteService = Depends(get_note_service)
):
    service.delete_note(note_id, current_user.model_dump())
