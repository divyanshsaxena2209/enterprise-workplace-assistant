"""Authenticated onboarding endpoints that avoid browser-side Supabase table access."""

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from supabase import Client

from app.core.enums import UserRole
from app.db.supabase import get_supabase_client
from app.dependencies.auth import require_employee, require_management
from app.schemas.profile import ProfileResponse

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])

_PROGRESS_WITH_STEP = (
    "id, step_id, status, notes, completion_date, "
    "onboarding_steps ( id, step_name, description, step_order )"
)


class ProgressUpdateRequest(BaseModel):
    status: Literal["PENDING", "IN_PROGRESS", "COMPLETED", "BLOCKED"]
    completion_date: datetime | None = None


class StepOrderItem(BaseModel):
    step_id: str = Field(min_length=1, max_length=64)
    step_order: int = Field(ge=0)


class StepOrderBatchRequest(BaseModel):
    items: list[StepOrderItem]


class AddOnboardingStepRequest(BaseModel):
    profile_id: str = Field(min_length=1, max_length=64)
    step_name: str = Field(min_length=1, max_length=128)
    description: str = Field(default="Custom step added by management.", max_length=1000)
    step_order: int = Field(ge=0)


@router.get("/my-progress")
def get_my_onboarding_progress(
    current_user: ProfileResponse = Depends(require_employee),
    db: Client = Depends(get_supabase_client),
) -> list[dict]:
    """Employees can read only progress rows belonging to their own profile ID."""
    try:
        result = (
            db.table("employee_onboarding_progress")
            .select(_PROGRESS_WITH_STEP)
            .eq("employee_id", str(current_user.id))
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to retrieve onboarding progress.") from exc
    return result.data or []


@router.get("/management/progress")
def get_management_onboarding_progress(
    _current_user: ProfileResponse = Depends(require_management),
    db: Client = Depends(get_supabase_client),
) -> dict:
    """Management-only employee progress and hired-application context."""
    try:
        profiles = (
            db.table("profiles")
            .select(
                "id, full_name, email, department, job_title, employee_id, "
                "employee_onboarding_progress ("
                "id, step_id, status, notes, completion_date, "
                "onboarding_steps ( id, step_name, description, step_order )"
                ")"
            )
            .execute()
        )
        applications = (
            db.table("applications")
            .select("id, jobs(title, department)")
            .in_("status", ["Hired", "HIRED"])
            .eq("is_deleted", False)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to retrieve management onboarding data.") from exc
    return {"profiles": profiles.data or [], "applications": applications.data or []}


@router.patch("/management/progress/{progress_id}")
def update_onboarding_progress(
    progress_id: str,
    body: ProgressUpdateRequest,
    _current_user: ProfileResponse = Depends(require_management),
    db: Client = Depends(get_supabase_client),
) -> dict:
    """Management-only status/completion-date update for one onboarding row."""
    try:
        result = (
            db.table("employee_onboarding_progress")
            .update({
                "status": body.status,
                "completion_date": body.completion_date.isoformat() if body.completion_date else None,
            })
            .eq("id", progress_id)
            .select("id, status, completion_date")
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to update onboarding progress.") from exc
    if not result.data:
        raise HTTPException(status_code=404, detail="Onboarding progress row not found.")
    return result.data[0]


@router.patch("/management/steps/order")
def reorder_onboarding_steps(
    body: StepOrderBatchRequest,
    _current_user: ProfileResponse = Depends(require_management),
    db: Client = Depends(get_supabase_client),
) -> dict:
    """Management-only reordering of existing step definitions."""
    if not body.items:
        raise HTTPException(status_code=422, detail="At least one step order is required.")
    step_ids = [item.step_id for item in body.items]
    if len(set(step_ids)) != len(step_ids):
        raise HTTPException(status_code=422, detail="Each step may appear only once in an order update.")
    try:
        for item in body.items:
            result = (
                db.table("onboarding_steps")
                .update({"step_order": item.step_order})
                .eq("id", item.step_id)
                .select("id")
                .execute()
            )
            if not result.data:
                raise HTTPException(status_code=404, detail="An onboarding step was not found.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to reorder onboarding steps.") from exc
    return {"success": True}


@router.delete("/management/progress/{progress_id}")
def delete_onboarding_progress(
    progress_id: str,
    _current_user: ProfileResponse = Depends(require_management),
    db: Client = Depends(get_supabase_client),
) -> dict:
    """Remove one employee's step assignment without deleting a shared step definition."""
    try:
        result = (
            db.table("employee_onboarding_progress")
            .delete()
            .eq("id", progress_id)
            .select("id")
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to remove onboarding step.") from exc
    if not result.data:
        raise HTTPException(status_code=404, detail="Onboarding progress row not found.")
    return {"success": True}


@router.post("/management/progress/steps")
def add_onboarding_step(
    body: AddOnboardingStepRequest,
    _current_user: ProfileResponse = Depends(require_management),
    db: Client = Depends(get_supabase_client),
) -> dict:
    """Create a step definition and assign it to a specific employee profile."""
    step_name = body.step_name.strip()
    if not step_name:
        raise HTTPException(status_code=422, detail="Step name cannot be blank.")

    try:
        profile_result = (
            db.table("profiles")
            .select("id, role")
            .eq("id", body.profile_id)
            .limit(1)
            .execute()
        )
        if not profile_result.data:
            raise HTTPException(status_code=404, detail="Employee profile not found.")
        if profile_result.data[0].get("role") != UserRole.EMPLOYEE.value:
            raise HTTPException(status_code=422, detail="Onboarding steps can only be assigned to employee profiles.")

        step_result = (
            db.table("onboarding_steps")
            .insert({
                "step_name": step_name,
                "description": body.description,
                "step_order": body.step_order,
                "template_id": None,
            })
            .select("*")
            .execute()
        )
        if not step_result.data:
            raise HTTPException(status_code=500, detail="Onboarding step was not created.")
        step = step_result.data[0]

        try:
            progress_result = (
                db.table("employee_onboarding_progress")
                .insert({
                    "employee_id": body.profile_id,
                    "step_id": step["id"],
                    "status": "PENDING",
                    "notes": "",
                })
                .select("*")
                .execute()
            )
            if not progress_result.data:
                raise HTTPException(status_code=500, detail="Onboarding step was not assigned.")
        except Exception:
            try:
                db.table("onboarding_steps").delete().eq("id", step["id"]).execute()
            except Exception:
                pass
            raise
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to add onboarding step.") from exc
    return {"progress": progress_result.data[0], "step": step}
