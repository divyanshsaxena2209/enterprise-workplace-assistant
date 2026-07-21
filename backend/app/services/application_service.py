"""
Application Service
Handles business logic for candidate applications.
"""

from typing import List, Optional
from uuid import UUID
from supabase import Client

from fastapi import BackgroundTasks
from app.core.exceptions import ValidationError, DatabaseError, AuthorizationError
from app.repositories.application_repository import ApplicationRepository
from app.repositories.job_repository import JobRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.pipeline_repository import PipelineRepository
from app.schemas.application import ApplicationCreate, ApplicationResponse, ApplicationListResponse, ApplicationDetailResponse
from app.schemas.interview import InterviewCreate, InterviewRespond, InterviewResponse

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
        self.pipeline_repo = PipelineRepository(client)

    def create_application(self, application_data: ApplicationCreate, user_id: str | UUID, background_tasks: BackgroundTasks = None) -> ApplicationResponse:
        """
        Validates entities and creates a new application.
        """
        # 1. Verify Job exists
        try:
            self.job_repo.get_job_or_raise(str(application_data.job_id))
        except Exception as exc:
            raise ValidationError(f"Job with ID {application_data.job_id} does not exist: {exc}")

        # 2. Verify Candidate exists
        try:
            self.candidate_repo.get_candidate_by_id(str(application_data.candidate_id))
        except Exception as e:
            raise ValidationError(f"Candidate with ID {application_data.candidate_id} does not exist. Inner Err: {str(e)}")

        # 3. Verify Resume exists
        res = self.client.table("resumes").select("id").eq("id", str(application_data.resume_id)).execute()
        if not res.data:
            raise ValidationError(f"Resume with ID {application_data.resume_id} does not exist.")

        # 4. Prevent duplicate applications
        existing = self.client.table("applications").select("id").eq("job_id", str(application_data.job_id)).eq("candidate_id", str(application_data.candidate_id)).eq("is_deleted", False).execute()
        if existing.data:
            raise ValidationError("Candidate has already applied for this job.")

        # 5. Create Application
        data = application_data.model_dump(mode="json")
        data["user_id"] = str(user_id)
        data["status"] = "Applied"

        created_app = self.repo.create_application(data)

        # 6. Automatic AI Evaluation (run in background)
        def _run_ai_evaluation(app_id: str, client: Client):
            try:
                from app.services.matching_service import MatchingService
                import logging
                logger = logging.getLogger(__name__)
                matching_svc = MatchingService(client)
                matching_svc.evaluate_application(app_id)
            except Exception as exc:
                logger = logging.getLogger(__name__)
                logger.error("Automatic AI evaluation failed for application %s: %s", app_id, exc)

        if background_tasks:
            background_tasks.add_task(_run_ai_evaluation, created_app.id, self.client)
        else:
            _run_ai_evaluation(created_app.id, self.client)

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

    def reject_application(self, application_id: str | UUID, user_id: str | UUID, notes: Optional[str] = None):
        """
        Rejects an application and logs the history.
        """
        # Get old status
        app_detail = self.repo.get_application(application_id)
        old_status = app_detail.application.status
        
        self.pipeline_repo.update_application_status(application_id, "Rejected")
        
        # Log history
        history_data = {
            "application_id": str(application_id),
            "old_status": old_status,
            "new_status": "Rejected",
            "changed_by": str(user_id),
            "notes": notes or "Candidate rejected."
        }
        self.pipeline_repo.insert_status_history(history_data)
        
    def schedule_interview(self, application_id: str | UUID, interview_data: InterviewCreate, user_id: str | UUID) -> InterviewResponse:
        """
        Schedules an interview for a candidate.
        """
        app_detail = self.repo.get_application(application_id)
        old_status = app_detail.application.status

        data = interview_data.model_dump(exclude_unset=True)
        data["application_id"] = str(application_id)
        # Fix datetime serialization for Supabase
        if "scheduled_at" in data and data["scheduled_at"]:
            data["scheduled_at"] = data["scheduled_at"].isoformat()
            
        res = self.client.table("interviews").insert(data).execute()
        if not res.data:
            raise DatabaseError("Failed to schedule interview.")
            
        new_interview = InterviewResponse.model_validate(res.data[0])
        
        self.pipeline_repo.update_application_status(application_id, "Interview Scheduled")
        
        history_data = {
            "application_id": str(application_id),
            "old_status": old_status,
            "new_status": "Interview Scheduled",
            "changed_by": str(user_id),
            "notes": "Interview scheduled."
        }
        self.pipeline_repo.insert_status_history(history_data)
        
        return new_interview

    def respond_interview(self, application_id: str | UUID, interview_id: str | UUID, respond_data: InterviewRespond, user_id: str | UUID) -> InterviewResponse:
        """
        Allows an employee to respond to an interview request.
        """
        app_detail = self.repo.get_application(application_id)
        if str(app_detail.application.user_id) != str(user_id):
            raise AuthorizationError("You do not have permission to respond to this interview.")
            
        res = self.client.table("interviews").update({
            "status": respond_data.status,
            "candidate_notes": respond_data.candidate_notes
        }).eq("id", str(interview_id)).eq("application_id", str(application_id)).execute()
        
        if not res.data:
            raise DatabaseError("Failed to respond to interview. It may not exist.")
            
        return InterviewResponse.model_validate(res.data[0])
