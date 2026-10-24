"""Management dashboard aggregates backed by the trusted service-role client."""

from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from app.db.supabase import get_supabase_client
from app.dependencies.auth import require_management
from app.schemas.profile import ProfileResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/management-summary")
def get_management_summary(
    _current_user: ProfileResponse = Depends(require_management),
    db: Client = Depends(get_supabase_client),
) -> dict:
    """Return management overview counts; employees cannot access these totals."""
    try:
        jobs = (
            db.table("jobs")
            .select("id", count="exact", head=True)
            .eq("is_deleted", False)
            .eq("status", "Published")
            .execute()
        )
        candidates = (
            db.table("candidates")
            .select("id", count="exact", head=True)
            .eq("is_deleted", False)
            .execute()
        )
        applications = (
            db.table("applications")
            .select("id", count="exact", head=True)
            .eq("is_deleted", False)
            .execute()
        )
        employees = (
            db.table("profiles")
            .select("id", count="exact", head=True)
            .in_("role", ["EMPLOYEE", "MANAGEMENT", "HR", "ADMIN"])
            .eq("is_active", True)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to load management dashboard statistics.") from exc

    return {
        "jobsCount": jobs.count or 0,
        "candidatesCount": candidates.count or 0,
        "applicationsCount": applications.count or 0,
        "employeesCount": employees.count or 0,
    }
