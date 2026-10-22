"""Role-protected onboarding routes."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.enums import UserRole
from app.db.supabase import get_db
from app.dependencies.auth import require_authenticated_user, require_management
from app.schemas.profile import ProfileResponse
from app.services.workflow_engine import WorkflowEngine
from app.services.rag_service import RAGService

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


class CreateEmployeeRequest(BaseModel):
    user_id: str
    full_name: str
    email: str
    department: str
    role: str
    template_id: str


class AIChatRequest(BaseModel):
    query: str
    employee_id: str


def _get_employee_or_404(db, employee_id: str) -> dict:
    response = (
        db.table("employees")
        .select("id,user_id,full_name,department,role")
        .eq("id", employee_id)
        .limit(1)
        .execute()
    )
    if not response.data:
        raise HTTPException(status_code=404, detail="Employee not found.")
    return response.data[0]


def _assert_employee_scope(employee: dict, current_user: ProfileResponse) -> None:
    """Managers may administer all employees; employees may access only their own row."""
    if current_user.role == UserRole.MANAGEMENT:
        return
    if (
        str(current_user.id) == "00000000-0000-0000-0000-000000000000"
        or str(employee.get("user_id")) != str(current_user.id)
    ):
        raise HTTPException(
            status_code=403,
            detail="You may only access your own onboarding information.",
        )


@router.post("/employees")
def onboard_new_employee(
    req: CreateEmployeeRequest,
    current_user: ProfileResponse = Depends(require_management),
    db=Depends(get_db),
):
    """Create an employee record and instantiate the onboarding workflow. Management only."""
    try:
        emp_data = {
            "user_id": req.user_id,
            "full_name": req.full_name,
            "email": req.email,
            "department": req.department,
            "role": req.role,
            "status": "Onboarding",
        }
        response = db.table("employees").insert(emp_data).execute()
        if not response.data:
            raise HTTPException(status_code=500, detail="Employee record was not created.")
        employee_id = response.data[0]["id"]

        WorkflowEngine.instantiate_template_for_employee(db, employee_id, req.template_id)
        WorkflowEngine.notify_user(
            db,
            req.user_id,
            "Welcome to the team!",
            "Your onboarding checklist is ready.",
            "/onboarding",
        )
        return {"status": "success", "employee_id": employee_id}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to create onboarding record.") from exc


@router.get("/tasks/{employee_id}")
def get_employee_tasks(
    employee_id: str,
    current_user: ProfileResponse = Depends(require_authenticated_user),
    db=Depends(get_db),
):
    """Employees can read their own tasks; Management can read any employee's tasks."""
    try:
        employee = _get_employee_or_404(db, employee_id)
        _assert_employee_scope(employee, current_user)
        tasks = db.table("onboarding_tasks").select("*").eq("employee_id", employee_id).execute()
        return tasks.data
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to retrieve onboarding tasks.") from exc


@router.post("/chat")
def onboarding_assistant_chat(
    req: AIChatRequest,
    current_user: ProfileResponse = Depends(require_authenticated_user),
    db=Depends(get_db),
):
    """Employees may query the onboarding assistant for themselves; Management can assist any employee."""
    try:
        employee = _get_employee_or_404(db, req.employee_id)
        _assert_employee_scope(employee, current_user)

        tasks_response = (
            db.table("onboarding_tasks")
            .select("title,status,due_date")
            .eq("employee_id", req.employee_id)
            .eq("status", "Pending")
            .execute()
        )
        pending_tasks = tasks_response.data

        retrieved_chunks = RAGService.semantic_search(
            req.query,
            department_filter=employee.get("department"),
            top_k=3,
        )
        system_context = (
            f"You are assisting {employee.get('full_name', 'the employee')}, "
            f"a {employee.get('role', 'employee')} in the "
            f"{employee.get('department', 'company')} department. "
            f"Their pending tasks are: {pending_tasks}."
        )
        augmented_query = f"[SYSTEM INFO: {system_context}]\n\nUser Query: {req.query}"
        response_text = RAGService.generate_rag_response(augmented_query, retrieved_chunks)
        return {"response": response_text, "sources": retrieved_chunks}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to answer the onboarding question.") from exc
