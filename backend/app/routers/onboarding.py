from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.db.supabase import get_db
from app.services.workflow_engine import WorkflowEngine
from app.services.rag_service import RAGService

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])

class CreateEmployeeRequest(BaseModel):
    user_id: str # Assume user is pre-created in IdP/users table
    full_name: str
    email: str
    department: str
    role: str
    template_id: str

class AIChatRequest(BaseModel):
    query: str
    employee_id: str

@router.post("/employees")
def onboard_new_employee(req: CreateEmployeeRequest, db=Depends(get_db)):
    """Creates an employee record and kicks off the onboarding workflow."""
    try:
        # 1. Create Employee
        emp_data = {
            "user_id": req.user_id,
            "full_name": req.full_name,
            "email": req.email,
            "department": req.department,
            "role": req.role,
            "status": "Onboarding"
        }
        res = db.table("employees").insert(emp_data).execute()
        employee_id = res.data[0]["id"]
        
        # 2. Trigger Workflow Engine to assign tasks
        WorkflowEngine.instantiate_template_for_employee(db, employee_id, req.template_id)
        
        # 3. Notify the employee
        WorkflowEngine.notify_user(
            db, 
            req.user_id, 
            "Welcome to the team!", 
            "Your onboarding checklist is ready.", 
            "/onboarding"
        )
        
        return {"status": "success", "employee_id": employee_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tasks/{employee_id}")
def get_employee_tasks(employee_id: str, db=Depends(get_db)):
    try:
        tasks = db.table("onboarding_tasks").select("*").eq("employee_id", employee_id).execute()
        return tasks.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
def onboarding_assistant_chat(req: AIChatRequest, db=Depends(get_db)):
    """AI Copilot integrated with RAG, tailored for the onboarding context."""
    try:
        # 1. Fetch employee context
        emp_res = db.table("employees").select("*").eq("id", req.employee_id).execute()
        if not emp_res.data:
            raise HTTPException(status_code=404, detail="Employee not found")
        emp = emp_res.data[0]
        
        # 2. Fetch pending tasks to provide context
        tasks_res = db.table("onboarding_tasks").select("title, status, due_date").eq("employee_id", req.employee_id).eq("status", "Pending").execute()
        pending_tasks = tasks_res.data
        
        # 3. Retrieve RAG chunks
        # We can pass the employee's department to filter ChromaDB for relevant SOPs
        retrieved_chunks = RAGService.semantic_search(req.query, department_filter=emp.get("department"), top_k=3)
        
        # 4. Generate highly contextualized prompt
        system_context = f"You are assisting {emp['full_name']}, a new {emp['role']} in the {emp['department']} department. They have the following pending tasks: {pending_tasks}."
        
        # 5. Call RAG (We extend RAGService's base behavior slightly by injecting the system_context)
        # Note: we are reusing the existing method and appending our context to the query for simplicity
        augmented_query = f"[SYSTEM INFO: {system_context}]\n\nUser Query: {req.query}"
        
        response_text = RAGService.generate_rag_response(augmented_query, retrieved_chunks)
        
        return {"response": response_text, "sources": retrieved_chunks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
