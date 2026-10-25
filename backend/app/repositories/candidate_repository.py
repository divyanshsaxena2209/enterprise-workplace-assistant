"""
Candidate Repository
Handles database operations for candidates and resumes.
"""

import logging
from typing import Dict, Any, List, Optional
from supabase import Client

from app.core.exceptions import DatabaseError, NotFoundError
from app.schemas.candidate import CandidateResponse, CandidateDetailResponse
from app.schemas.resume import ResumeResponse


logger = logging.getLogger(__name__)


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
        candidate_id = None
        try:
            candidate_res = self._db.table("candidates").insert(candidate_data).execute()
            if not candidate_res.data:
                raise DatabaseError("Failed to insert candidate.")
            candidate_id = candidate_res.data[0]["id"]

            # The live Supabase schema uses file_name, file_url, parsed_json and
            # uploaded_at. Build an explicit payload with actual database columns.
            file_name = resume_data.get("file_name") or resume_data.get("filename")
            file_url = resume_data.get("file_url")
            if not isinstance(file_name, str) or not file_name.strip():
                raise ValueError("Resume file name is required.")
            if not isinstance(file_url, str) or not file_url.strip():
                raise ValueError("Resume file URL is required.")
            parsed_json = resume_data.get("parsed_json")
            if parsed_json is None:
                parsed_json = resume_data.get("parsed_data", {})

            resume_record = {
                "candidate_id": candidate_id,
                "file_name": file_name,
                "file_url": file_url,
                "parsed_json": parsed_json,
            }
            resume_res = self._db.table("resumes").insert(resume_record).execute()
            if not resume_res.data:
                raise DatabaseError("Failed to insert resume.")
            resume_id = resume_res.data[0]["id"]

            return candidate_id, resume_id
        except Exception as exc:
            # Supabase REST calls are separate transactions. If resume persistence
            # fails after candidate creation, remove the candidate to avoid an orphan.
            if candidate_id is not None:
                try:
                    self._db.table("candidates").delete().eq("id", candidate_id).execute()
                except Exception as cleanup_exc:
                    logger.error(
                        "Candidate rollback after resume persistence failure failed (exception_type=%s).",
                        type(cleanup_exc).__name__,
                    )
            logger.error(
                "Candidate/resume persistence failed (exception_type=%s, code=%s).",
                type(exc).__name__,
                getattr(exc, "code", None),
            )
            raise DatabaseError(
                f"Failed to save candidate and resume data to database ({type(exc).__name__})."
            ) from exc

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
            
            cand_res = self._db.table("candidates").select("*").eq("id", candidate_id).eq("is_deleted", False).execute()
            if not cand_res.data:
                raise NotFoundError(f"Candidate with ID '{candidate_id}' not found.")
            candidate = CandidateResponse.model_validate(cand_res.data[0])

            
            resume_res = self._db.table("resumes").select("*").eq("candidate_id", candidate_id).order("created_at", desc=True).limit(1).execute()
            resume = None
            if resume_res.data:
                resume_row = dict(resume_res.data[0])
                file_url = resume_row.get("file_url") or ""
                if file_url.startswith(("s3://", "supabase://")):
                    from app.services.object_storage import create_resume_download_url
                    storage_provider, resume_key = file_url.split("://", 1)
                    resume_row["file_url"] = create_resume_download_url(
                        resume_key, storage_provider=storage_provider
                    )
                else:
                    # Older rows stored Supabase public-URL-shaped values.
                    # Convert recognized storage paths into a fresh signed URL.
                    from app.services.object_storage import (
                        create_resume_download_url,
                        extract_supabase_object_key_from_url,
                    )
                    legacy_key = extract_supabase_object_key_from_url(
                        file_url, prefix="resumes"
                    )
                    if legacy_key:
                        resume_row["file_url"] = create_resume_download_url(
                            legacy_key, storage_provider="supabase"
                        )
                resume = ResumeResponse.model_validate(resume_row)

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
            
            self.get_candidate_by_id(candidate_id)
            
            self._db.table("candidates").update({"is_deleted": True}).eq("id", candidate_id).execute()
        except NotFoundError:
            raise
        except Exception as exc:
            raise DatabaseError(f"Failed to delete candidate: {exc}") from exc
