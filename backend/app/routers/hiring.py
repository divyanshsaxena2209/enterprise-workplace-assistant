from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import supabase_admin
from app.dependencies.auth import require_management
from app.schemas.profile import ProfileResponse
from app.schemas.hiring import ScreenResumeRequest, ScreenResumeResponse
from app.services.resume_parser import ResumeParserService
from app.services.candidate_evaluator import CandidateEvaluatorService
from typing import Dict, Any

router = APIRouter()

@router.post("/screen-resume", response_model=ScreenResumeResponse, status_code=status.HTTP_201_CREATED)
def screen_resume(
    payload: ScreenResumeRequest,
    current_user: ProfileResponse = Depends(require_management)
):
    """
    Downloads a candidate's resume from the configured private storage provider, extracts its text,
    screens it using Gemini AI against the specified Job, scores it,
    saves the parsed details into the PostgreSQL candidates table, and returns the result.
    """
    job_id = payload.job_id
    resume_file_path = payload.resume_file_path

    
    try:
        job_res = supabase_admin.table("jobs").select("*").eq("id", job_id).execute()
        if not job_res.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job description with ID '{job_id}' not found"
            )
        job = job_res.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving job from database: {str(e)}"
        )

    
    try:
        if resume_file_path.startswith("s3://"):
            from app.services.object_storage import download_s3_object_bytes
            s3_key = resume_file_path.removeprefix("s3://")
            file_data = download_s3_object_bytes(s3_key, prefix="resumes")
        elif resume_file_path.startswith("resumes/"):
            from app.services.object_storage import download_s3_object_bytes
            file_data = download_s3_object_bytes(resume_file_path, prefix="resumes")
        elif resume_file_path.startswith("supabase://"):
            from app.services.object_storage import download_supabase_object_bytes
            supabase_key = resume_file_path.removeprefix("supabase://")
            file_data = download_supabase_object_bytes(supabase_key, prefix="resumes")
        elif resume_file_path.startswith(("http://", "https://")):
            from app.services.object_storage import (
                download_supabase_object_bytes,
                extract_supabase_object_key_from_url,
            )
            supabase_key = extract_supabase_object_key_from_url(
                resume_file_path, prefix="resumes"
            )
            if not supabase_key:
                raise ValueError("Unsupported legacy resume URL.")
            file_data = download_supabase_object_bytes(supabase_key, prefix="resumes")
        else:
            # Backward compatibility for resumes uploaded before the S3 cutover.
            file_data = supabase_admin.storage.from_("resumes").download(resume_file_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to download resume. Check the private storage key and execution-role permissions.",
        ) from e

    
    try:
        resume_parser = ResumeParserService()
        resume_text = resume_parser.extract_text(file_data, resume_file_path)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse resume document content: {str(e)}"
        )

    
    try:
        
        parsed_resume = resume_parser.parse_with_ai(resume_text)
        
        
        from app.schemas.hiring import JobResponse
        job_model = JobResponse(**job)
        evaluator = CandidateEvaluatorService()
        eval_result = evaluator.evaluate_against_job(job_model, parsed_resume)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI model screening failed: {str(e)}"
        )

    
    
    experience_list = [exp.model_dump() for exp in parsed_resume.experience]

    full_name = parsed_resume.full_name or ""
    name_parts = full_name.split(" ", 1)
    first_name = name_parts[0] if len(name_parts) > 0 else ""
    last_name = name_parts[1] if len(name_parts) > 1 else ""

    candidate_data = {
        "job_id": job_id,
        "first_name": first_name,
        "last_name": last_name,
        "email": parsed_resume.email,
        "resume_file_path": resume_file_path,
        "suitability_score": eval_result.match_percentage,
        "match_explanation": eval_result.ai_summary,
        "parsed_skills": parsed_resume.skills,
        "parsed_experience": experience_list,
        "status": "SCREENING"
    }

    try:
        insert_res = supabase_admin.table("candidates").insert(candidate_data).execute()
        if not insert_res.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to persist candidate records to database."
            )
        candidate = insert_res.data[0]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database persistence failed: {str(e)}"
        )

    return ScreenResumeResponse(
        candidate_id=candidate["id"],
        first_name=candidate["first_name"],
        last_name=candidate["last_name"],
        email=candidate["email"],
        suitability_score=candidate["suitability_score"],
        match_explanation=candidate["match_explanation"],
        parsed_skills=candidate["parsed_skills"],
        parsed_experience=candidate["parsed_experience"],
        status=candidate["status"]
    )
