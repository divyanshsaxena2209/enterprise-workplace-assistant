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
from app.schemas.candidate_score import CandidateScoreResponse

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
                "*, jobs(*), candidates(*), resumes(*), candidate_scores(*)"
            ).eq("id", str(application_id)).eq("is_deleted", False).execute()
            
            if not res.data:
                raise NotFoundError(f"Application with ID '{application_id}' not found.")
            
            row = res.data[0]
            
            app_data = {k: v for k, v in row.items() if k not in ("jobs", "candidates", "resumes", "candidate_scores")}
            application = ApplicationResponse.model_validate(app_data)
            
            job = JobResponse.model_validate(row["jobs"]) if row.get("jobs") else None
            candidate = CandidateResponse.model_validate(row["candidates"]) if row.get("candidates") else None
            resume = ResumeResponse.model_validate(row["resumes"]) if row.get("resumes") else None
            
            score = None
            if row.get("candidate_scores"):
                scores = row["candidate_scores"]
                if isinstance(scores, list) and len(scores) > 0:
                    score = CandidateScoreResponse.model_validate(scores[0])
                elif isinstance(scores, dict):
                    score = CandidateScoreResponse.model_validate(scores)

            interviews = []
            try:
                from app.schemas.interview import InterviewResponse
                int_res = self._db.table("interviews").select("*").eq("application_id", str(application_id)).execute()
                if int_res.data:
                    interviews = [InterviewResponse.model_validate(i) for i in int_res.data]
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Could not fetch interviews: {e}")

            if score and job:
                try:
                    score_res = self._db.table("candidate_scores").select("match_percentage, applications!inner(job_id)").eq("applications.job_id", str(job.id)).order("match_percentage", desc=True).limit(1).execute()
                    if score_res.data and len(score_res.data) > 0:
                        m_score = score_res.data[0]["match_percentage"]
                        if m_score == 0:
                            score.relative_score = 0
                        else:
                            score.relative_score = min(100, int((score.match_percentage / m_score) * 100))
                except Exception:
                    score.relative_score = score.match_percentage

            return ApplicationDetailResponse(
                application=application,
                job=job,
                candidate=candidate,
                resume=resume,
                score=score,
                interviews=interviews
            )
        except NotFoundError:
            raise
        except Exception as exc:
            # Check if this is a PostgREST schema cache error (PGRST200)
            exc_str = str(exc)
            if 'PGRST200' in exc_str or 'Could not find a relationship' in exc_str:
                # Fallback: Sequential fetching
                res = self._db.table("applications").select("*").eq("id", str(application_id)).eq("is_deleted", False).execute()
                if not res.data:
                    raise NotFoundError(f"Application with ID '{application_id}' not found.")
                row = res.data[0]
                application = ApplicationResponse.model_validate(row)
                
                # Fetch related
                job_res = self._db.table("jobs").select("*").eq("id", str(application.job_id)).execute()
                job = JobResponse.model_validate(job_res.data[0]) if job_res.data else None
                
                cand_res = self._db.table("candidates").select("*").eq("id", str(application.candidate_id)).execute()
                candidate = CandidateResponse.model_validate(cand_res.data[0]) if cand_res.data else None
                
                res_res = self._db.table("resumes").select("*").eq("id", str(application.resume_id)).execute()
                resume = ResumeResponse.model_validate(res_res.data[0]) if res_res.data else None
                
                score_res = self._db.table("candidate_scores").select("*").eq("application_id", str(application.id)).execute()
                score = CandidateScoreResponse.model_validate(score_res.data[0]) if score_res.data else None
                
                from app.schemas.interview import InterviewResponse
                interviews = []
                try:
                    int_res = self._db.table("interviews").select("*").eq("application_id", str(application.id)).execute()
                    if int_res.data:
                        interviews = [InterviewResponse.model_validate(i) for i in int_res.data]
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning(f"Fallback: Could not fetch interviews: {e}")
                
                if score and job:
                    try:
                        max_res = self._db.table("candidate_scores").select("match_percentage, applications!inner(job_id)").eq("applications.job_id", str(job.id)).order("match_percentage", desc=True).limit(1).execute()
                        if max_res.data and len(max_res.data) > 0:
                            m_score = max_res.data[0]["match_percentage"]
                            score.relative_score = 0 if m_score == 0 else min(100, int((score.match_percentage / m_score) * 100))
                    except Exception:
                        score.relative_score = score.match_percentage
                
                
                return ApplicationDetailResponse(
                    application=application, job=job, candidate=candidate, resume=resume, score=score, interviews=interviews
                )
                
            print(f"DEBUG: Raising DatabaseError because exc_str={exc_str}")
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

            # Ensure we always select candidates and scores for the dashboard UI
            needs_job = department is not None
            
            select_clause = "*"
            if needs_job:
                select_clause += ", jobs!inner(*)"
            else:
                select_clause += ", jobs(*)"
            if needs_score:
                select_clause += ", candidate_scores!inner(*)"
            else:
                select_clause += ", candidate_scores(*)"
                
            if needs_candidate:
                select_clause += ", candidates!inner(*)"
            else:
                select_clause += ", candidates(*)"

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
                app = ApplicationResponse.model_validate(app_data)
                
                # Attach nested data for dashboard rendering
                if row.get("candidates"):
                    app.candidate = CandidateResponse.model_validate(row["candidates"])
                if row.get("candidate_scores"):
                    scores = row["candidate_scores"]
                    if isinstance(scores, list) and len(scores) > 0:
                        app.score = CandidateScoreResponse.model_validate(scores[0])
                    elif isinstance(scores, dict):
                        app.score = CandidateScoreResponse.model_validate(scores)
                        
                if row.get("jobs"):
                    app.job = JobResponse.model_validate(row["jobs"])
                        
                items.append(app)

            total = res.count if res.count is not None else len(items)
            
            # ATTACH RELATIVE SCORES
            job_ids = list(set(str(app.job_id) for app in items if app.job_id and app.score))
            if job_ids:
                try:
                    # Query max match_percentage for each job using an inner join on applications
                    score_res = self._db.table("candidate_scores").select("match_percentage, applications!inner(job_id)").in_("applications.job_id", job_ids).execute()
                    max_scores = {}
                    for r in score_res.data:
                        j_id = str(r["applications"]["job_id"])
                        sc = r["match_percentage"]
                        if j_id not in max_scores or sc > max_scores[j_id]:
                            max_scores[j_id] = sc
                    
                    for app in items:
                        if app.score and app.job_id:
                            j_id = str(app.job_id)
                            m_score = max_scores.get(j_id, 100)
                            if m_score == 0:
                                app.score.relative_score = 0
                            else:
                                app.score.relative_score = min(100, int((app.score.match_percentage / m_score) * 100))
                except Exception as ex:
                    # Fallback to absolute score
                    for app in items:
                        if app.score:
                            app.score.relative_score = app.score.match_percentage

            # Fetch interviews for these applications
            app_ids = [str(app.id) for app in items]
            if app_ids:
                try:
                    from app.schemas.interview import InterviewResponse
                    int_res = self._db.table("interviews").select("*").in_("application_id", app_ids).execute()
                    if int_res.data:
                        interviews_by_app = {}
                        for i_data in int_res.data:
                            i_app_id = str(i_data["application_id"])
                            if i_app_id not in interviews_by_app:
                                interviews_by_app[i_app_id] = []
                            interviews_by_app[i_app_id].append(InterviewResponse.model_validate(i_data))
                        for app in items:
                            app.interviews = interviews_by_app.get(str(app.id), [])
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning(f"Could not fetch interviews for list: {e}")

            return items, total
        except Exception as exc:
            # Check if this is a PostgREST schema cache error (PGRST200)
            exc_str = str(exc)
            if 'PGRST200' in exc_str or 'Could not find a relationship' in exc_str:
                # Fallback: Sequential fetching without joins
                try:
                    # Query just applications
                    base_query = self._db.table("applications").select("*", count="exact").eq("is_deleted", False)
                    if job_id: base_query = base_query.eq("job_id", str(job_id))
                    if candidate_id: base_query = base_query.eq("candidate_id", str(candidate_id))
                    if status: base_query = base_query.eq("status", status)
                    if user_id: base_query = base_query.eq("user_id", str(user_id))
                    
                    base_query = base_query.order("created_at", desc=sort_desc)
                    base_query = base_query.range(skip, skip + limit - 1)
                    
                    res = base_query.execute()
                    
                    items = []
                    for row in res.data:
                        app = ApplicationResponse.model_validate(row)
                        
                        # Fetch Candidate
                        if app.candidate_id:
                            cand_res = self._db.table("candidates").select("*").eq("id", str(app.candidate_id)).execute()
                            if cand_res.data:
                                app.candidate = CandidateResponse.model_validate(cand_res.data[0])
                        
                        # Fetch Score
                        score_res = self._db.table("candidate_scores").select("*").eq("application_id", str(app.id)).execute()
                        if score_res.data:
                            app.score = CandidateScoreResponse.model_validate(score_res.data[0])
                            # Relative score fallback
                            app.score.relative_score = app.score.match_percentage
                            
                        # Fetch Job
                        if app.job_id:
                            job_res = self._db.table("jobs").select("*").eq("id", str(app.job_id)).execute()
                            if job_res.data:
                                app.job = JobResponse.model_validate(job_res.data[0])

                        # Fetch Interviews
                        try:
                            from app.schemas.interview import InterviewResponse
                            int_res = self._db.table("interviews").select("*").eq("application_id", str(app.id)).execute()
                            if int_res.data:
                                app.interviews = [InterviewResponse.model_validate(i) for i in int_res.data]
                        except Exception as e:
                            import logging
                            logging.getLogger(__name__).warning(f"Could not fetch interviews for fallback: {e}")

                        items.append(app)
                        
                    total = res.count if res.count is not None else len(items)
                    return items, total
                except Exception as inner_exc:
                    raise DatabaseError(f"Failed to list applications (fallback): {inner_exc}") from inner_exc

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
