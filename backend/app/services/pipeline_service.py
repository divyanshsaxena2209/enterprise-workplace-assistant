"""
Pipeline Service
Enforces state transitions and workflow management for applications.
"""

from uuid import UUID
from supabase import Client

from app.core.exceptions import ValidationError, DatabaseError, NotFoundError
from app.repositories.pipeline_repository import PipelineRepository
from app.repositories.application_repository import ApplicationRepository
from app.schemas.pipeline import PipelineDashboardResponse

class PipelineService:
    # Valid status transitions mapping
    VALID_TRANSITIONS = {
        "Applied": ["Under Review"],
        "Under Review": ["Shortlisted", "Rejected"],
        "Shortlisted": ["Interview Scheduled", "Rejected"],
        "Interview Scheduled": ["Interview Completed"],
        "Interview Completed": ["Offer Extended", "Rejected"],
        "Offer Extended": ["Hired", "Rejected"],
        "Hired": [],
        "Rejected": []
    }

    def __init__(self, client: Client):
        self.client = client
        self.pipeline_repo = PipelineRepository(client)
        self.app_repo = ApplicationRepository(client)

    def transition_application(self, application_id: str | UUID, new_status: str, changed_by: str | UUID, notes: str | None = None) -> None:
        """
        Moves an application to a new status, validating the transition and recording the history.
        """
        try:
            # 1. Fetch current application status
            app_detail = self.app_repo.get_application(application_id)
            current_status = app_detail.application.status

            # 2. Validate transition
            if new_status == current_status:
                return # No change needed

            allowed_next_states = self.VALID_TRANSITIONS.get(current_status, [])
            if new_status not in allowed_next_states:
                raise ValidationError(f"Invalid status transition from '{current_status}' to '{new_status}'. Allowed transitions: {allowed_next_states}")

            # 3. Perform update (simulate transaction via sequence since Supabase py client lacks true transaction grouping easily)
            # Update the status
            self.pipeline_repo.update_application_status(application_id, new_status)

            # Insert history
            history_data = {
                "application_id": str(application_id),
                "old_status": current_status,
                "new_status": new_status,
                "changed_by": str(changed_by),
                "notes": notes
            }
            self.pipeline_repo.insert_status_history(history_data)

        except NotFoundError:
            raise
        except ValidationError:
            raise
        except Exception as exc:
            raise DatabaseError(f"Failed to transition application status: {exc}") from exc

    def get_history(self, application_id: str | UUID):
        """Returns the status history for a given application."""
        return self.pipeline_repo.get_history_by_application(application_id)

    def get_dashboard_metrics(self) -> PipelineDashboardResponse:
        """Returns the grouped counts of applications in the pipeline."""
        metrics_dict = self.pipeline_repo.get_pipeline_metrics()
        return PipelineDashboardResponse(**metrics_dict)
