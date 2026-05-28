from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import require_role, supabase_admin
from app.schemas.hiring import ScreenResumeRequest, ScreenResumeResponse
from app.services.resume_parser import extract_resume_text, screen_resume_with_ai
from typing import Dict, Any

router = APIRouter()

@router.post("/screen-resume", response_model=ScreenResumeResponse, status_code=status.HTTP_201_CREATED)
def screen_resume(
    payload: ScreenResumeRequest,
    current_user: Dict[str, Any] = Depends(require_role(["HR_ADMIN", "SUPER_ADMIN"]))
):
    """
    Downloads a candidate's resume from Supabase storage, extracts its text,
    screens it using GPT-4o against the specified Job, scores it,
    saves the parsed details into the PostgreSQL candidates table, and returns the result.
    """
    job_id = payload.job_id
    resume_file_path = payload.resume_file_path

    # 1. Fetch the Job details from PostgreSQL
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

    # 2. Download the resume file from Supabase Storage (bucket 'resumes')
    try:
        # Expected path format is "job-uuid/filename.pdf" or simply "filename.pdf"
        file_data = supabase_admin.storage.from_("resumes").download(resume_file_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to download resume from Storage: {str(e)}. Ensure the file exists in the 'resumes' bucket."
        )

    # 3. Extract text from resume bytes
    try:
        resume_text = extract_resume_text(file_data, resume_file_path)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse resume document content: {str(e)}"
        )

    # 4. Invoke OpenAI GPT-4o screening pipeline
    try:
        screening_result = screen_resume_with_ai(
            resume_text=resume_text,
            job_title=job["title"],
            job_description=job["description"],
            job_requirements=job.get("requirements", [])
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI model screening failed: {str(e)}"
        )

    # 5. Save the parsed candidate details into PostgreSQL
    # Convert ExperienceDetail list to raw JSON lists
    experience_list = [exp.model_dump() for exp in screening_result.parsed_experience]

    candidate_data = {
        "job_id": job_id,
        "first_name": screening_result.first_name,
        "last_name": screening_result.last_name,
        "email": screening_result.email,
        "resume_file_path": resume_file_path,
        "suitability_score": screening_result.suitability_score,
        "match_explanation": screening_result.match_explanation,
        "parsed_skills": screening_result.parsed_skills,
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
