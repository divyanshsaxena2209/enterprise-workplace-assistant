from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from app.schemas.ats import ApplicationCreate, ApplicationResponse
from app.db.supabase import get_db

router = APIRouter(prefix="/applications", tags=["Applications"])

@router.post("/", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_application(application: ApplicationCreate, db=Depends(get_db)):
    try:
        res = db.table("applications").insert(application.model_dump()).execute()
        if not res.data:
            raise HTTPException(status_code=400, detail="Could not create application")
        return res.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/job/{job_id}", response_model=List[ApplicationResponse])
def get_applications_by_job(job_id: UUID, db=Depends(get_db)):
    try:
        res = db.table("applications").select("*, candidates(*), resumes(*)").eq("job_id", str(job_id)).execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
