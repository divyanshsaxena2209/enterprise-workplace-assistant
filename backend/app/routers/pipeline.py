from fastapi import APIRouter, Depends, Query, status
from typing import List
from uuid import UUID
from supabase import Client

from app.db.supabase import get_supabase_client
from app.dependencies.auth import require_management
from app.schemas.profile import ProfileResponse
from app.schemas.pipeline import StatusTransitionRequest, ApplicationStatusHistoryResponse, PipelineDashboardResponse
from app.services.pipeline_service import PipelineService

router = APIRouter(tags=["Pipeline"])

def get_pipeline_service(client: Client = Depends(get_supabase_client)) -> PipelineService:
    return PipelineService(client)

@router.patch(
    "/applications/{application_id}/status",
    status_code=status.HTTP_200_OK,
    summary="Update Application Status",
    description="Moves candidate through pipeline. Records history. Management only."
)
def update_application_status(
    application_id: UUID,
    transition: StatusTransitionRequest,
    current_user: ProfileResponse = Depends(require_management),
    service: PipelineService = Depends(get_pipeline_service)
):
    service.transition_application(
        application_id=application_id,
        new_status=transition.status,
        changed_by=current_user.id,
        notes=transition.notes
    )
    return {"message": "Status updated successfully"}

@router.get(
    "/applications/{application_id}/history",
    response_model=List[ApplicationStatusHistoryResponse],
    summary="Get Status History",
    description="Retrieves the audit history of status changes. Management only."
)
def get_application_history(
    application_id: UUID,
    current_user: ProfileResponse = Depends(require_management),
    service: PipelineService = Depends(get_pipeline_service)
):
    return service.get_history(application_id)

@router.get(
    "/applications/pipeline",
    response_model=PipelineDashboardResponse,
    summary="Get Pipeline Dashboard Metrics",
    description="Retrieves grouped counts of all applications in each status stage. Management only."
)
def get_pipeline_dashboard(
    current_user: ProfileResponse = Depends(require_management),
    service: PipelineService = Depends(get_pipeline_service)
):
    return service.get_dashboard_metrics()
