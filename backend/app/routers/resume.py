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

MAX_FILE_SIZE = 10 * 1024 * 1024  


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

    
    parser = ResumeParserService()
    raw_text = parser.extract_text(file_bytes, file.filename)
    parsed_data = parser.parse_with_ai(raw_text)

    
    client = get_supabase_client()
    
    
    try:
        from app.core.config import settings
        from app.services.object_storage import upload_knowledge_document

        stored = upload_knowledge_document(
            file.filename,
            file_bytes,
            file.content_type or "application/octet-stream",
            prefix="resumes",
        )
        # Persist a stable S3 object key rather than an expiring presigned URL.
        # CandidateRepository signs it when an authorised user requests details.
        if stored["storage_provider"] == "s3":
            file_url = f"s3://{stored['file_key']}"
        else:
            file_url = stored["file_url"]
    except Exception as exc:
        raise DatabaseError(
            f"Failed to upload resume to {settings.STORAGE_PROVIDER} object storage: {type(exc).__name__}"
        ) from exc

    
    repo = CandidateRepository(client)
    
    candidate_data = {
        "full_name": parsed_data.full_name or "Unknown Candidate",
        "email": parsed_data.email,
        "phone": parsed_data.phone,
        
        
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
