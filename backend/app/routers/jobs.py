"""
Jobs Router
Handles endpoints for Job Management.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from app.db.supabase import get_supabase_client
from app.core.enums import JobStatus
from app.dependencies.auth import get_current_user, require_management
from app.schemas.profile import ProfileResponse
from app.schemas.common import ErrorResponse, PaginatedResponse, SuccessResponse
from app.schemas.job import JobCreate, JobUpdate, JobResponse
from app.services.job_service import JobService

router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
)


def _get_job_service() -> JobService:
    return JobService(get_supabase_client())


@router.post(
    "",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new job",
    description="Create a new job listing. Requires MANAGEMENT role. Status will default to Draft.",
    responses={
        201: {"description": "Job created.", "model": JobResponse},
        401: {"description": "Not authenticated.", "model": ErrorResponse},
        403: {"description": "Forbidden. Requires Management role.", "model": ErrorResponse},
        422: {"description": "Validation error.", "model": ErrorResponse},
    },
)
def create_job(
    body: JobCreate,
    current_user: ProfileResponse = Depends(require_management),
    svc: JobService = Depends(_get_job_service),
) -> JobResponse:
    """**Create a Job.**"""
    return svc.create_job(body, current_user)


@router.get(
    "",
    response_model=PaginatedResponse[JobResponse],
    summary="List jobs",
    description="Retrieves a paginated list of jobs. Employees only see Published jobs. Management sees all. Supports search and filters.",
    responses={
        200: {"description": "List of jobs.", "model": PaginatedResponse[JobResponse]},
        401: {"description": "Not authenticated.", "model": ErrorResponse},
    },
)
def list_jobs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by title or department"),
    department: Optional[str] = Query(None, description="Filter by department"),
    job_status: Optional[JobStatus] = Query(None, description="Filter by status (Management only)"),
    location: Optional[str] = Query(None, description="Filter by location"),
    current_user: ProfileResponse = Depends(get_current_user),
    svc: JobService = Depends(_get_job_service),
) -> PaginatedResponse[JobResponse]:
    """**List Jobs.**"""
    skip = (page - 1) * page_size
    jobs = svc.list_jobs(
        current_user=current_user,
        skip=skip,
        limit=page_size,
        search=search,
        department=department,
        status=job_status,
        location=location
    )
    
    return PaginatedResponse(
        data=jobs,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    summary="Get job details",
    description="Retrieves a job by ID. Employees can only view Published jobs.",
    responses={
        200: {"description": "Job details.", "model": JobResponse},
        401: {"description": "Not authenticated.", "model": ErrorResponse},
        403: {"description": "Forbidden.", "model": ErrorResponse},
        404: {"description": "Job not found.", "model": ErrorResponse},
    },
)
def get_job(
    job_id: str,
    current_user: ProfileResponse = Depends(get_current_user),
    svc: JobService = Depends(_get_job_service),
) -> JobResponse:
    """**Get Job details.**"""
    return svc.get_job(job_id, current_user)


@router.patch(
    "/{job_id}",
    response_model=JobResponse,
    summary="Update a job",
    description="Partially update a job. Requires MANAGEMENT role.",
    responses={
        200: {"description": "Job updated.", "model": JobResponse},
        401: {"description": "Not authenticated.", "model": ErrorResponse},
        403: {"description": "Forbidden. Requires Management role.", "model": ErrorResponse},
        404: {"description": "Job not found.", "model": ErrorResponse},
        422: {"description": "Validation error.", "model": ErrorResponse},
    },
)
def update_job(
    job_id: str,
    body: JobUpdate,
    current_user: ProfileResponse = Depends(require_management),
    svc: JobService = Depends(_get_job_service),
) -> JobResponse:
    """**Update a Job.**"""
    return svc.update_job(job_id, body, current_user)


@router.patch(
    "/{job_id}/publish",
    response_model=JobResponse,
    summary="Publish a job",
    description="Changes job status to Published. Requires MANAGEMENT role.",
    responses={
        200: {"description": "Job published.", "model": JobResponse},
        401: {"description": "Not authenticated.", "model": ErrorResponse},
        403: {"description": "Forbidden. Requires Management role.", "model": ErrorResponse},
        404: {"description": "Job not found.", "model": ErrorResponse},
    },
)
def publish_job(
    job_id: str,
    current_user: ProfileResponse = Depends(require_management),
    svc: JobService = Depends(_get_job_service),
) -> JobResponse:
    """**Publish a Job.**"""
    return svc.publish_job(job_id, current_user)


@router.patch(
    "/{job_id}/archive",
    response_model=JobResponse,
    summary="Archive a job",
    description="Changes job status to Archived. Requires MANAGEMENT role.",
    responses={
        200: {"description": "Job archived.", "model": JobResponse},
        401: {"description": "Not authenticated.", "model": ErrorResponse},
        403: {"description": "Forbidden. Requires Management role.", "model": ErrorResponse},
        404: {"description": "Job not found.", "model": ErrorResponse},
    },
)
def archive_job(
    job_id: str,
    current_user: ProfileResponse = Depends(require_management),
    svc: JobService = Depends(_get_job_service),
) -> JobResponse:
    """**Archive a Job.**"""
    return svc.archive_job(job_id, current_user)


@router.delete(
    "/{job_id}",
    response_model=SuccessResponse,
    summary="Delete a job",
    description="Soft deletes a job. Requires MANAGEMENT role.",
    responses={
        200: {"description": "Job deleted.", "model": SuccessResponse},
        401: {"description": "Not authenticated.", "model": ErrorResponse},
        403: {"description": "Forbidden. Requires Management role.", "model": ErrorResponse},
        404: {"description": "Job not found.", "model": ErrorResponse},
    },
)
def delete_job(
    job_id: str,
    current_user: ProfileResponse = Depends(require_management),
    svc: JobService = Depends(_get_job_service),
) -> SuccessResponse:
    """**Soft delete a Job.**"""
    svc.delete_job(job_id, current_user)
    return SuccessResponse(message="Job successfully deleted.")
