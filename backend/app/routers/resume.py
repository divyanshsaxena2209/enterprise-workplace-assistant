"""
Resume Router
Handles resume uploads, parsing, and initial candidate creation.
"""

import uuid
from fastapi import APIRouter, Depends, UploadFile, File, status

from app.db.supabase import get_supabase_client
from app.dependencies.auth import get_current_user
from app.schemas.profile import ProfileResponse
from app.schemas.resume import ResumeUploadResponse
from app.schemas.common import ErrorResponse
from app.services.resume_parser import ResumeParserService
from app.repositories.candidate_repository import CandidateRepository
from app.core.exceptions import BadRequestError, DatabaseError

router = APIRouter(
    prefix="/resume",
    tags=["Resume Screening"],
)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post(
    "/upload",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and process a resume",
    description="Uploads a PDF or DOCX resume (max 10MB). Extracts text, parses into structured data using AI, evaluates the candidate, and stores the results.",
    responses={
        201: {"description": "Resume processed successfully.", "model": ResumeUploadResponse},
        400: {"description": "Bad Request (e.g., file too large, invalid format).", "model": ErrorResponse},
        401: {"description": "Not authenticated.", "model": ErrorResponse},
        500: {"description": "Internal Server Error or AI Service Failure.", "model": ErrorResponse},
    },
)
def upload_resume(
    file: UploadFile = File(...),
    current_user: ProfileResponse = Depends(get_current_user)
) -> ResumeUploadResponse:
    """
    **Uploads a candidate resume.**
    - Validates file type and size.
    - Uploads raw file to Supabase Storage.
    - Extracts raw text using PyPDF2 / docx2txt.
    - Parses text into structured JSON via Gemini AI.
    - Saves Candidate and Resume to database.
    """
    
    # 1. Validation
    if not file.filename:
        raise BadRequestError("No filename provided.")
        
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["pdf", "doc", "docx"]:
        raise BadRequestError("Only PDF and DOCX files are allowed.")

    file_bytes = file.file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise BadRequestError("File exceeds the 10MB size limit.")

    if len(file_bytes) == 0:
        raise BadRequestError("Uploaded file is empty.")

    # 2. Extract Text & Parse
    parser = ResumeParserService()
    raw_text = parser.extract_text(file_bytes, file.filename)
    parsed_data = parser.parse_with_ai(raw_text)

    # 3. Upload to Storage
    client = get_supabase_client()
    
    # Generate unique filename to prevent collisions
    unique_filename = f"{uuid.uuid4()}_{file.filename.replace(' ', '_')}"
    
    try:
        # Supabase Storage upload
        client.storage.from_("resumes").upload(
            path=unique_filename,
            file=file_bytes,
            file_options={"content-type": file.content_type}
        )
        
        # Get public URL
        file_url = client.storage.from_("resumes").get_public_url(unique_filename)
    except Exception as exc:
        raise DatabaseError(f"Failed to upload resume to storage: {exc}") from exc

    # 4. Save to Database
    repo = CandidateRepository(client)
    
    candidate_data = {
        "full_name": parsed_data.full_name or "Unknown Candidate",
        "email": parsed_data.email,
        "phone": parsed_data.phone,
        # Extract linkedin/portfolio from text if needed, but omitted for now as it's not strictly in schema.
        # Could add basic extraction logic here if needed.
    }
    
    resume_data = {
        "file_url": file_url,
        "parsed_data": parsed_data.model_dump(),
    }
    
    candidate_id, resume_id = repo.create_candidate_with_resume(
        candidate_data=candidate_data,
        resume_data=resume_data
    )

    return ResumeUploadResponse(candidate_id=candidate_id, resume_id=resume_id)
