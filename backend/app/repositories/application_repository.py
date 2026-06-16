"""
Application Repository
Handles database operations for the candidate applications module.
"""

from typing import Dict, Any, List, Optional
from uuid import UUID
from supabase import Client

from app.core.exceptions import DatabaseError, NotFoundError
from app.schemas.application import ApplicationResponse, ApplicationDetailResponse
from app.schemas.job import JobResponse
from app.schemas.candidate import CandidateResponse
from app.schemas.resume import ResumeResponse

class ApplicationRepository:
    """Data access object for the applications table."""

    def __init__(self, client: Client) -> None:
        self._db = client

    def create_application(self, application_data: Dict[str, Any]) -> ApplicationResponse:
        """
        Creates a new application in the database.
        Raises DatabaseError on failure (e.g. unique constraint violation).
        """
        try:
            res = self._db.table("applications").insert(application_data).execute()
            if not res.data:
                raise DatabaseError("Failed to insert application.")
            return ApplicationResponse.model_validate(res.data[0])
        except Exception as exc:
            # We catch specific duplicate errors in the service layer using string matching if needed,
            # but raising DatabaseError preserves the stack and base type.
            raise DatabaseError(f"Failed to save application: {exc}") from exc

    def get_application(self, application_id: str | UUID) -> ApplicationDetailResponse:
        """
        Gets a single application by ID, including related Job, Candidate, and Resume.
        """
        try:
            res = self._db.table("applications").select(
                "*, jobs(*), candidates(*), resumes(*)"
            ).eq("id", str(application_id)).eq("is_deleted", False).execute()
            
            if not res.data:
                raise NotFoundError(f"Application with ID '{application_id}' not found.")
            
            row = res.data[0]
            
            app_data = {k: v for k, v in row.items() if k not in ("jobs", "candidates", "resumes")}
            application = ApplicationResponse.model_validate(app_data)
            
            job = JobResponse.model_validate(row["jobs"]) if row.get("jobs") else None
            candidate = CandidateResponse.model_validate(row["candidates"]) if row.get("candidates") else None
            resume = ResumeResponse.model_validate(row["resumes"]) if row.get("resumes") else None

            return ApplicationDetailResponse(
                application=application,
                job=job,
                candidate=candidate,
                resume=resume
            )
        except NotFoundError:
            raise
        except Exception as exc:
            raise DatabaseError(f"Failed to fetch application: {exc}") from exc

    def list_applications(
        self, 
        skip: int = 0, 
        limit: int = 20, 
        job_id: Optional[str | UUID] = None,
        candidate_id: Optional[str | UUID] = None,
        status: Optional[str] = None,
        user_id: Optional[str | UUID] = None,
        department: Optional[str] = None,
        recommendation: Optional[str] = None,
        min_score: Optional[int] = None,
        max_score: Optional[int] = None,
        sort_by: str = "created_at",
        sort_desc: bool = True
    ) -> tuple[List[ApplicationResponse], int]:
        """
        Lists applications with optional filtering and pagination.
        Supports filtering by nested relationships (jobs, candidate_scores).
        """
        try:
            # Determine if we need to inner join tables for filtering/sorting
            needs_job = department is not None
            needs_score = recommendation is not None or min_score is not None or max_score is not None or sort_by == "match_score"
            needs_candidate = sort_by == "candidate_name"

            select_clause = "*"
            if needs_job:
                select_clause += ", jobs!inner(*)"
            if needs_score:
                select_clause += ", candidate_scores!inner(*)"
            if needs_candidate:
                select_clause += ", candidates!inner(*)"

            query = self._db.table("applications").select(select_clause, count="exact").eq("is_deleted", False)
            
            # Base filters
            if job_id:
                query = query.eq("job_id", str(job_id))
            if candidate_id:
                query = query.eq("candidate_id", str(candidate_id))
            if status:
                query = query.eq("status", status)
            if user_id:
                query = query.eq("user_id", str(user_id))
                
            # Nested filters
            if department:
                query = query.eq("jobs.department", department)
            if recommendation:
                query = query.eq("candidate_scores.recommendation", recommendation)
            if min_score is not None:
                query = query.gte("candidate_scores.match_percentage", min_score)
            if max_score is not None:
                query = query.lte("candidate_scores.match_percentage", max_score)
                
            # Sorting
            if sort_by == "match_score":
                query = query.order("match_percentage", foreignTable="candidate_scores", desc=sort_desc)
            elif sort_by == "candidate_name":
                query = query.order("full_name", foreignTable="candidates", desc=sort_desc)
            else:
                query = query.order("created_at", desc=sort_desc)

            query = query.range(skip, skip + limit - 1)
            
            res = query.execute()
            
            items = []
            for row in res.data:
                # Strip out the nested joined data before validating to the base schema
                app_data = {k: v for k, v in row.items() if k not in ("jobs", "candidate_scores", "candidates")}
                items.append(ApplicationResponse.model_validate(app_data))

            total = res.count if res.count is not None else len(items)
            
            return items, total
        except Exception as exc:
            raise DatabaseError(f"Failed to list applications: {exc}") from exc

    def soft_delete_application(self, application_id: str | UUID) -> None:
        """
        Soft deletes an application.
        """
        try:
            res = self._db.table("applications").update({"is_deleted": True}).eq("id", str(application_id)).execute()
            if not res.data:
                raise NotFoundError(f"Application with ID '{application_id}' not found.")
        except NotFoundError:
            raise
        except Exception as exc:
            raise DatabaseError(f"Failed to delete application: {exc}") from exc
