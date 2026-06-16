"""
Candidate Score Repository
Handles database operations for AI evaluations and scores.
"""

from typing import List, Optional, Tuple
from uuid import UUID
from supabase import Client

from app.core.exceptions import DatabaseError, NotFoundError
from app.schemas.candidate_score import CandidateScoreResponse, CandidateScoreCreate

class CandidateScoreRepository:
    """Data access object for candidate AI scores."""

    def __init__(self, client: Client) -> None:
        self._db = client

    def upsert_score(self, score_data: CandidateScoreCreate) -> CandidateScoreResponse:
        """
        Creates or updates a score for a specific application.
        """
        try:
            # We use upsert because there is a UNIQUE constraint on application_id
            data_dict = score_data.model_dump()
            data_dict["application_id"] = str(data_dict["application_id"])
            
            # Using Supabase's upsert matching on the unique constraint (on conflict)
            res = self._db.table("candidate_scores").upsert(
                data_dict, 
                on_conflict="application_id"
            ).execute()
            
            if not res.data:
                raise DatabaseError("Failed to save candidate score.")
                
            return CandidateScoreResponse.model_validate(res.data[0])
        except Exception as exc:
            raise DatabaseError(f"Failed to upsert candidate score: {exc}") from exc

    def get_score_by_application_id(self, application_id: str | UUID) -> CandidateScoreResponse:
        """
        Retrieves the evaluation score for a given application ID.
        """
        try:
            res = self._db.table("candidate_scores").select("*").eq("application_id", str(application_id)).execute()
            if not res.data:
                raise NotFoundError(f"No evaluation score found for application ID '{application_id}'.")
            return CandidateScoreResponse.model_validate(res.data[0])
        except NotFoundError:
            raise
        except Exception as exc:
            raise DatabaseError(f"Failed to fetch candidate score: {exc}") from exc

    def list_scores(
        self, 
        skip: int = 0, 
        limit: int = 20, 
        recommendation: Optional[str] = None,
        min_score: Optional[int] = None
    ) -> Tuple[List[CandidateScoreResponse], int]:
        """
        Lists evaluation scores with optional filtering and pagination.
        Returns a tuple of (items, total_count).
        """
        try:
            query = self._db.table("candidate_scores").select("*", count="exact")
            
            if recommendation:
                query = query.eq("recommendation", recommendation)
            if min_score is not None:
                query = query.gte("match_percentage", min_score)
                
            query = query.range(skip, skip + limit - 1).order("evaluated_at", desc=True)
            
            res = query.execute()
            
            items = [CandidateScoreResponse.model_validate(row) for row in res.data]
            total = res.count if res.count is not None else len(items)
            
            return items, total
        except Exception as exc:
            raise DatabaseError(f"Failed to list candidate scores: {exc}") from exc
