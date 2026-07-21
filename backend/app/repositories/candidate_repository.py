"""
Candidate Repository
Handles database operations for candidates and resumes.
"""

from typing import Dict, Any, List, Optional
from supabase import Client

from app.core.exceptions import DatabaseError, NotFoundError
from app.schemas.candidate import CandidateResponse, CandidateDetailResponse
from app.schemas.resume import ResumeResponse


class CandidateRepository:
    """Data access object for candidate-related tables."""

    def __init__(self, client: Client) -> None:
        self._db = client

    def create_candidate_with_resume(
        self,
        candidate_data: Dict[str, Any],
        resume_data: Dict[str, Any]
    ) -> tuple[str, str]:
        """
        Creates a candidate and their resume.
        Returns the new candidate ID and resume ID.
        """
        try:
            # 1. Create candidate
            candidate_res = self._db.table("candidates").insert(candidate_data).execute()
            if not candidate_res.data:
                raise DatabaseError("Failed to insert candidate.")
            candidate_id = candidate_res.data[0]["id"]

            # 2. Add candidate_id to related data
            resume_data["candidate_id"] = candidate_id

            # 3. Create resume
            resume_res = self._db.table("resumes").insert(resume_data).execute()
            resume_id = resume_res.data[0]["id"]

            return candidate_id, resume_id
        except Exception as exc:
            raise DatabaseError(f"Failed to save candidate data to database: {exc}") from exc

    def get_candidates(self, skip: int = 0, limit: int = 20, search: Optional[str] = None) -> List[CandidateResponse]:
        """
        Get a paginated list of active (non-deleted) candidates.
        """
        try:
            query = self._db.table("candidates").select("*").eq("is_deleted", False)
            
            if search:
                query = query.or_(f"full_name.ilike.%{search}%,email.ilike.%{search}%")
            
            query = query.range(skip, skip + limit - 1).order("created_at", desc=True)
            response = query.execute()
            
            return [CandidateResponse.model_validate(row) for row in response.data]
        except Exception as exc:
            raise DatabaseError(f"Failed to fetch candidates: {exc}") from exc

    def get_candidate_by_id(self, candidate_id: str) -> CandidateDetailResponse:
        """
        Get a candidate by ID, including their resume.
        """
        try:
            # Fetch Candidate
            cand_res = self._db.table("candidates").select("*").eq("id", candidate_id).eq("is_deleted", False).execute()
            if not cand_res.data:
                raise NotFoundError(f"Candidate with ID '{candidate_id}' not found.")
            candidate = CandidateResponse.model_validate(cand_res.data[0])

            # Fetch Resume
            resume_res = self._db.table("resumes").select("*").eq("candidate_id", candidate_id).order("created_at", desc=True).limit(1).execute()
            resume = ResumeResponse.model_validate(resume_res.data[0]) if resume_res.data else None

            return CandidateDetailResponse(
                candidate=candidate,
                resume=resume
            )
        except NotFoundError:
            raise
        except Exception as exc:
            raise DatabaseError(f"Failed to fetch candidate details: {exc}") from exc

    def soft_delete_candidate(self, candidate_id: str) -> None:
        """
        Soft delete a candidate by setting is_deleted = True.
        """
        try:
            # Check existence first
            self.get_candidate_by_id(candidate_id)
            
            self._db.table("candidates").update({"is_deleted": True}).eq("id", candidate_id).execute()
        except NotFoundError:
            raise
        except Exception as exc:
            raise DatabaseError(f"Failed to delete candidate: {exc}") from exc
