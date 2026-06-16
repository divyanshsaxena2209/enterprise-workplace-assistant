from fastapi import APIRouter, Depends, Query, status
from typing import Optional
from uuid import UUID
from supabase import Client

from app.db.supabase import get_supabase_client
from app.dependencies.auth import get_current_user, require_management, require_employee, require_authenticated_user
from app.schemas.profile import ProfileResponse
from app.schemas.application import (
    ApplicationCreate, 
    ApplicationResponse, 
    ApplicationListResponse, 
    ApplicationDetailResponse
)
from app.repositories.application_repository import ApplicationRepository
from app.services.application_service import ApplicationService

router = APIRouter(prefix="/applications", tags=["Applications"])

def get_application_service(client: Client = Depends(get_supabase_client)) -> ApplicationService:
    repo = ApplicationRepository(client)
    return ApplicationService(repo, client)

@router.post(
    "/",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit an application",
    description="Submit a new application for a job. Associates the current authenticated employee with the application."
)
def create_application(
    application: ApplicationCreate,
    current_user: ProfileResponse = Depends(require_authenticated_user),
    service: ApplicationService = Depends(get_application_service)
):
    return service.create_application(application, user_id=current_user.id)


@router.get(
    "/",
    response_model=ApplicationListResponse,
    summary="List applications",
    description="List all applications. This endpoint is restricted to Management. Supports filtering by job_id, candidate_id, and status."
)
def list_applications(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    job_id: Optional[UUID] = None,
    candidate_id: Optional[UUID] = None,
    status: Optional[str] = None,
    current_user: ProfileResponse = Depends(require_management),
    service: ApplicationService = Depends(get_application_service)
):
    return service.list_applications(
        current_user=current_user,
        page=page,
        limit=limit,
        job_id=job_id,
        candidate_id=candidate_id,
        status=status
    )


@router.get(
    "/my",
    response_model=ApplicationListResponse,
    summary="List my applications",
    description="List applications submitted by the current authenticated employee."
)
def list_my_applications(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    job_id: Optional[UUID] = None,
    status: Optional[str] = None,
    current_user: ProfileResponse = Depends(require_employee),
    service: ApplicationService = Depends(get_application_service)
):
    return service.list_applications(
        current_user=current_user,
        page=page,
        limit=limit,
        job_id=job_id,
        status=status
    )


@router.get(
    "/{application_id}",
    response_model=ApplicationDetailResponse,
    summary="Get application details",
    description="Get details for a specific application. Management can view any; Employees can view only their own."
)
def get_application_details(
    application_id: UUID,
    current_user: ProfileResponse = Depends(require_authenticated_user),
    service: ApplicationService = Depends(get_application_service)
):
    return service.get_application(application_id, current_user)


@router.delete(
    "/{application_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft delete application",
    description="Soft deletes an application. This endpoint is restricted to Management."
)
def delete_application(
    application_id: UUID,
    current_user: ProfileResponse = Depends(require_management),
    service: ApplicationService = Depends(get_application_service)
):
    service.delete_application(application_id)
