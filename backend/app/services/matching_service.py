"""
Matching Service
Orchestrates the AI evaluation of an Application by bringing together Job and Resume data.
"""

from uuid import UUID
from typing import Optional
from supabase import Client

from app.core.exceptions import ValidationError, DatabaseError, ServiceUnavailableError, NotFoundError
from app.schemas.candidate_score import CandidateScoreCreate, CandidateScoreResponse
from app.repositories.application_repository import ApplicationRepository
from app.repositories.candidate_score_repository import CandidateScoreRepository
from app.services.candidate_evaluator import CandidateEvaluatorService
from app.schemas.resume import ParsedResumeData

class MatchingService:
    def __init__(self, client: Client):
        self.client = client
        self.app_repo = ApplicationRepository(client)
        self.score_repo = CandidateScoreRepository(client)
        self.evaluator = CandidateEvaluatorService()

    def evaluate_application(self, application_id: str | UUID) -> CandidateScoreResponse:
        """
        Retrieves the application, job, and parsed resume, then evaluates the candidate against the job.
        """
        # 1. Fetch Application Detail (which includes Job and Resume)
        try:
            app_detail = self.app_repo.get_application(application_id)
        except Exception as exc:
            raise NotFoundError(f"Could not retrieve application for evaluation: {exc}") from exc

        if not app_detail.job:
            raise ValidationError("Application does not have an associated Job.")
        if not app_detail.resume:
            raise ValidationError("Application does not have an associated Resume.")

        # Parse the JSONB parsed_data into our Pydantic model
        if not app_detail.resume.parsed_data:
            raise ValidationError("Resume has not been fully parsed yet. Cannot evaluate.")

        try:
            parsed_resume = ParsedResumeData.model_validate(app_detail.resume.parsed_data)
        except Exception as exc:
            raise ValidationError(f"Resume parsed data is malformed: {exc}") from exc

        # 2. Call Evaluator
        try:
            eval_result = self.evaluator.evaluate_against_job(app_detail.job, parsed_resume)
        except ServiceUnavailableError as exc:
            raise ServiceUnavailableError(f"Evaluation failed: {exc}") from exc
        except Exception as exc:
            raise ServiceUnavailableError(f"Unexpected error during evaluation: {exc}") from exc

        # 3. Save Score
        score_create = CandidateScoreCreate(
            application_id=application_id,
            match_percentage=eval_result.match_percentage,
            ai_summary=eval_result.ai_summary,
            strengths=eval_result.strengths,
            weaknesses=eval_result.weaknesses,
            recommendation=eval_result.recommendation
        )

        try:
            saved_score = self.score_repo.upsert_score(score_create)
            return saved_score
        except Exception as exc:
            raise DatabaseError(f"Failed to save candidate evaluation score: {exc}") from exc

    def get_application_score(self, application_id: str | UUID) -> CandidateScoreResponse:
        return self.score_repo.get_score_by_application_id(application_id)
