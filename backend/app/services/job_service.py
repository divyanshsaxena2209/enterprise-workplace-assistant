"""
Job Service
Handles business logic, status transitions, and authorization for Jobs.
"""

from typing import List, Optional
from supabase import Client

from app.core.enums import JobStatus, UserRole
from app.core.exceptions import AuthorizationError, ValidationError
from app.schemas.job import JobCreate, JobUpdate, JobResponse
from app.schemas.profile import ProfileResponse
from app.repositories.job_repository import JobRepository


class JobService:
    """Service handling job listings and transitions."""

    def __init__(self, client: Client) -> None:
        self._repo = JobRepository(client)

    def create_job(self, data: JobCreate, current_user: ProfileResponse) -> JobResponse:
        """
        Create a new job. Only Management can do this.
        Always starts in DRAFT status.
        """
        if current_user.role != UserRole.MANAGEMENT:
            raise AuthorizationError("Only Management can create jobs.")

        job_data = data.model_dump()
        job_data["status"] = JobStatus.DRAFT.value
        job_data["created_by"] = current_user.id

        return self._repo.create_job(job_data)

    def update_job(self, job_id: str, data: JobUpdate, current_user: ProfileResponse) -> JobResponse:
        """
        Update a job. Only Management can do this.
        """
        if current_user.role != UserRole.MANAGEMENT:
            raise AuthorizationError("Only Management can update jobs.")

        updates = data.to_update_dict()
        return self._repo.update_job(job_id, updates)

    def get_job(self, job_id: str, current_user: ProfileResponse) -> JobResponse:
        """
        Get a job.
        Management can see any job. Employees can only see PUBLISHED jobs.
        """
        job = self._repo.get_job_or_raise(job_id)

        if current_user.role != UserRole.MANAGEMENT and job.status != JobStatus.PUBLISHED:
            raise AuthorizationError("You do not have permission to view this job.")

        return job

    def list_jobs(
        self,
        current_user: ProfileResponse,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        department: Optional[str] = None,
        status: Optional[JobStatus] = None,
        location: Optional[str] = None
    ) -> List[JobResponse]:
        """
        List jobs with filters.
        If Employee, override status to PUBLISHED.
        """
        effective_status = status
        
        if current_user.role != UserRole.MANAGEMENT:
            effective_status = JobStatus.PUBLISHED

        return self._repo.get_jobs(
            skip=skip,
            limit=limit,
            search=search,
            department=department,
            status=effective_status,
            location=location
        )

    def publish_job(self, job_id: str, current_user: ProfileResponse) -> JobResponse:
        """
        Publish a job. Only Management can do this.
        """
        if current_user.role != UserRole.MANAGEMENT:
            raise AuthorizationError("Only Management can publish jobs.")
            
        # Get job to ensure it exists
        job = self._repo.get_job_or_raise(job_id)
        
        if job.status == JobStatus.PUBLISHED:
            return job
            
        return self._repo.update_job(job_id, {"status": JobStatus.PUBLISHED.value})

    def archive_job(self, job_id: str, current_user: ProfileResponse) -> JobResponse:
        """
        Archive a job. Only Management can do this.
        """
        if current_user.role != UserRole.MANAGEMENT:
            raise AuthorizationError("Only Management can archive jobs.")
            
        return self._repo.update_job(job_id, {"status": JobStatus.ARCHIVED.value})

    def close_job(self, job_id: str, current_user: ProfileResponse) -> JobResponse:
        """
        Close a job. Only Management can do this.
        """
        if current_user.role != UserRole.MANAGEMENT:
            raise AuthorizationError("Only Management can close jobs.")
            
        return self._repo.update_job(job_id, {"status": JobStatus.CLOSED.value})

    def delete_job(self, job_id: str, current_user: ProfileResponse) -> None:
        """
        Soft delete a job. Only Management can do this.
        """
        if current_user.role != UserRole.MANAGEMENT:
            raise AuthorizationError("Only Management can delete jobs.")
            
        self._repo.soft_delete_job(job_id)
