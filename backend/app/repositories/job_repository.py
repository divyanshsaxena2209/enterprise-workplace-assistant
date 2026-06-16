"""
Job Repository
Handles database operations for the jobs table.
"""

from typing import Dict, Any, List, Optional
from supabase import Client

from app.core.exceptions import DatabaseError, NotFoundError
from app.core.enums import JobStatus
from app.schemas.job import JobResponse


class JobRepository:
    """Data access object for the jobs table."""

    def __init__(self, client: Client) -> None:
        self._db = client

    def create_job(self, job_data: Dict[str, Any]) -> JobResponse:
        """Creates a new job."""
        try:
            res = self._db.table("jobs").insert(job_data).execute()
            if not res.data:
                raise DatabaseError("Failed to insert job.")
            return JobResponse.model_validate(res.data[0])
        except Exception as exc:
            raise DatabaseError(f"Failed to save job to database: {exc}") from exc

    def update_job(self, job_id: str, updates: Dict[str, Any]) -> JobResponse:
        """Updates a job."""
        if not updates:
            return self.get_job_or_raise(job_id)
            
        try:
            res = self._db.table("jobs").update(updates).eq("id", job_id).execute()
            if not res.data:
                raise NotFoundError(f"Job with ID '{job_id}' not found.")
            return JobResponse.model_validate(res.data[0])
        except NotFoundError:
            raise
        except Exception as exc:
            raise DatabaseError(f"Failed to update job: {exc}") from exc

    def get_job_or_raise(self, job_id: str) -> JobResponse:
        """Get a single job by ID or raise NotFoundError."""
        try:
            res = self._db.table("jobs").select("*").eq("id", job_id).eq("is_deleted", False).execute()
            if not res.data:
                raise NotFoundError(f"Job with ID '{job_id}' not found.")
            return JobResponse.model_validate(res.data[0])
        except NotFoundError:
            raise
        except Exception as exc:
            raise DatabaseError(f"Failed to fetch job details: {exc}") from exc

    def get_jobs(
        self, 
        skip: int = 0, 
        limit: int = 20, 
        search: Optional[str] = None,
        department: Optional[str] = None,
        status: Optional[JobStatus] = None,
        location: Optional[str] = None
    ) -> List[JobResponse]:
        """
        Get a paginated list of active jobs with optional filtering and full-text search.
        """
        try:
            query = self._db.table("jobs").select("*").eq("is_deleted", False)
            
            if status:
                query = query.eq("status", status.value)
            
            if department:
                query = query.eq("department", department)
                
            if location:
                query = query.eq("location", location)
            
            if search:
                # Basic ilike search on title or department
                query = query.or_(f"title.ilike.%{search}%,department.ilike.%{search}%")
            
            query = query.range(skip, skip + limit - 1).order("created_at", desc=True)
            response = query.execute()
            
            return [JobResponse.model_validate(row) for row in response.data]
        except Exception as exc:
            raise DatabaseError(f"Failed to fetch jobs: {exc}") from exc

    def soft_delete_job(self, job_id: str) -> None:
        """Soft deletes a job by setting is_deleted = True."""
        try:
            # Check existence first
            self.get_job_or_raise(job_id)
            
            self._db.table("jobs").update({"is_deleted": True}).eq("id", job_id).execute()
        except NotFoundError:
            raise
        except Exception as exc:
            raise DatabaseError(f"Failed to delete job: {exc}") from exc
