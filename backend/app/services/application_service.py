"""
Application Service
Handles business logic for candidate applications.
"""

from typing import List, Optional
from uuid import UUID
from supabase import Client

from app.core.exceptions import ValidationError, DatabaseError, AuthorizationError
from app.repositories.application_repository import ApplicationRepository
from app.repositories.job_repository import JobRepository
from app.repositories.candidate_repository import CandidateRepository
from app.schemas.application import ApplicationCreate, ApplicationResponse, ApplicationListResponse, ApplicationDetailResponse

class ApplicationService:
    def __init__(
        self,
        application_repo: ApplicationRepository,
        client: Client
    ):
        self.repo = application_repo
        self.client = client
        self.job_repo = JobRepository(client)
        self.candidate_repo = CandidateRepository(client)

    def create_application(self, application_data: ApplicationCreate, user_id: str | UUID) -> ApplicationResponse:
        """
        Validates entities and creates a new application.
        """
        # 1. Verify Job exists
        try:
            self.job_repo.get_job_by_id(str(application_data.job_id))
        except Exception:
            raise ValidationError(f"Job with ID {application_data.job_id} does not exist.")

        # 2. Verify Candidate exists
        try:
            self.candidate_repo.get_candidate_by_id(str(application_data.candidate_id))
        except Exception:
            raise ValidationError(f"Candidate with ID {application_data.candidate_id} does not exist.")

        # 3. Verify Resume exists
        res = self.client.table("resumes").select("id").eq("id", str(application_data.resume_id)).execute()
        if not res.data:
            raise ValidationError(f"Resume with ID {application_data.resume_id} does not exist.")

        # 4. Prevent duplicate applications
        existing = self.client.table("applications").select("id").eq("job_id", str(application_data.job_id)).eq("candidate_id", str(application_data.candidate_id)).eq("is_deleted", False).execute()
        if existing.data:
            raise ValidationError("Candidate has already applied for this job.")

        # 5. Create Application
        data = application_data.model_dump()
        data["user_id"] = str(user_id)
        data["status"] = "Applied"

        created_app = self.repo.create_application(data)

        # 6. Automatic AI Evaluation
        try:
            from app.services.matching_service import MatchingService
            import logging
            logger = logging.getLogger(__name__)
            
            matching_svc = MatchingService(self.client)
            matching_svc.evaluate_application(created_app.id)
        except Exception as exc:
            # Log failure but do not roll back the successful application creation
            logger.error("Automatic AI evaluation failed for application %s: %s", created_app.id, exc)

        return created_app

    def get_application(self, application_id: str | UUID, current_user: dict) -> ApplicationDetailResponse:
        """
        Retrieves a single application. Enforces RBAC.
        """
        app_detail = self.repo.get_application(application_id)
        
        # Enforce RBAC
        # Management can view all. Employees can view only their own.
        if current_user.role not in ["ADMIN", "HR", "MANAGEMENT"]:
            if str(app_detail.application.user_id) != str(current_user.id):
                raise AuthorizationError("You do not have permission to view this application.")

        # Hydrate extra details (Score, History, Notes)
        try:
            from app.repositories.candidate_score_repository import CandidateScoreRepository
            score_repo = CandidateScoreRepository(self.client)
            app_detail.score = score_repo.get_score_by_application_id(application_id)
        except Exception:
            pass
            
        try:
            from app.repositories.pipeline_repository import PipelineRepository
            pipeline_repo = PipelineRepository(self.client)
            app_detail.history = pipeline_repo.get_history_by_application(application_id)
        except Exception:
            pass
            
        try:
            from app.repositories.recruiter_note_repository import RecruiterNoteRepository
            notes_repo = RecruiterNoteRepository(self.client)
            app_detail.notes = notes_repo.get_notes_by_application(application_id)
        except Exception:
            pass

        return app_detail

    def list_applications(
        self,
        current_user: dict,
        page: int = 1,
        limit: int = 20,
        job_id: Optional[str | UUID] = None,
        candidate_id: Optional[str | UUID] = None,
        status: Optional[str] = None,
        department: Optional[str] = None,
        recommendation: Optional[str] = None,
        min_score: Optional[int] = None,
        max_score: Optional[int] = None,
        sort_by: str = "created_at",
        sort_desc: bool = True
    ) -> ApplicationListResponse:
        """
        Lists applications with pagination and filtering. Enforces RBAC.
        """
        skip = (page - 1) * limit

        # If employee, force filter to their own applications
        user_id_filter = None
        if current_user.role not in ["ADMIN", "HR", "MANAGEMENT"]:
            user_id_filter = current_user.id

        items, total = self.repo.list_applications(
            skip=skip,
            limit=limit,
            job_id=job_id,
            candidate_id=candidate_id,
            status=status,
            user_id=user_id_filter,
            department=department,
            recommendation=recommendation,
            min_score=min_score,
            max_score=max_score,
            sort_by=sort_by,
            sort_desc=sort_desc
        )

        return ApplicationListResponse(
            items=items,
            total=total,
            page=page,
            limit=limit
        )

    def delete_application(self, application_id: str | UUID):
        """
        Soft deletes an application. (Management only, handled in router).
        """
        self.repo.soft_delete_application(application_id)
