from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from app.schemas.ats import JobCreate, JobResponse
from app.db.supabase import get_db

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(job: JobCreate, db=Depends(get_db)):
    try:
        res = db.table("jobs").insert(job.model_dump()).execute()
        if not res.data:
            raise HTTPException(status_code=400, detail="Could not create job")
        return res.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[JobResponse])
def get_jobs(db=Depends(get_db)):
    try:
        res = db.table("jobs").select("*").order("created_at", desc=True).execute()
        return res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: UUID, db=Depends(get_db)):
    try:
        res = db.table("jobs").select("*").eq("id", str(job_id)).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Job not found")
        return res.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
