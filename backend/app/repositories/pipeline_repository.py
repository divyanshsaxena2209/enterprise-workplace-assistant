"""
Pipeline Repository
Handles database operations for ATS workflow management and audit history.
"""

from typing import List, Dict, Any, Optional
from uuid import UUID
from supabase import Client

from app.core.exceptions import DatabaseError
from app.schemas.pipeline import ApplicationStatusHistoryResponse

class PipelineRepository:
    def __init__(self, client: Client) -> None:
        self._db = client

    def update_application_status(self, application_id: str | UUID, new_status: str) -> None:
        try:
            res = self._db.table("applications").update({"status": new_status}).eq("id", str(application_id)).execute()
            if not res.data:
                raise DatabaseError("Application status update failed or application not found.")
        except Exception as exc:
            raise DatabaseError(f"Failed to update application status: {exc}") from exc

    def insert_status_history(self, history_data: Dict[str, Any]) -> ApplicationStatusHistoryResponse:
        try:
            # history_data should contain: application_id, old_status, new_status, changed_by, notes
            res = self._db.table("application_status_history").insert(history_data).execute()
            if not res.data:
                raise DatabaseError("Failed to insert status history.")
            return ApplicationStatusHistoryResponse.model_validate(res.data[0])
        except Exception as exc:
            raise DatabaseError(f"Failed to save status history: {exc}") from exc

    def get_history_by_application(self, application_id: str | UUID) -> List[ApplicationStatusHistoryResponse]:
        try:
            res = self._db.table("application_status_history").select("*").eq("application_id", str(application_id)).order("created_at", desc=True).execute()
            return [ApplicationStatusHistoryResponse.model_validate(row) for row in res.data]
        except Exception as exc:
            raise DatabaseError(f"Failed to fetch application history: {exc}") from exc

    def get_pipeline_metrics(self) -> Dict[str, int]:
        """
        Calculates the count of applications grouped by status.
        Uses a raw RPC if possible, but since we want to avoid complex Supabase setups just for counts,
        we can fetch the counts via standard queries.
        Note: If the dataset gets large, an RPC grouping by status is highly recommended.
        """
        statuses = [
            "Applied", "Under Review", "Shortlisted", 
            "Interview Scheduled", "Interview Completed", 
            "Offer Extended", "Hired", "Rejected"
        ]
        
        metrics = {status.lower().replace(" ", "_"): 0 for status in statuses}
        
        try:
            # We can use multiple count queries, or fetch all active applications' statuses
            # For simplicity and given standard pagination, we'll run a single select of just the statuses
            # In a true enterprise scale, this should be a PostgreSQL view or RPC function `get_status_counts()`.
            res = self._db.table("applications").select("status").eq("is_deleted", False).execute()
            
            for row in res.data:
                status_key = row["status"].lower().replace(" ", "_")
                if status_key in metrics:
                    metrics[status_key] += 1
            
            return metrics
        except Exception as exc:
            raise DatabaseError(f"Failed to fetch pipeline metrics: {exc}") from exc
