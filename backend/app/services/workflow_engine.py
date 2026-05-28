import datetime
from pydantic import BaseModel
from typing import List, Dict, Any

class WorkflowEngine:
    @staticmethod
    def instantiate_template_for_employee(db, employee_id: str, template_id: str):
        """Fetches a template and creates onboarding tasks for the employee."""
        try:
            # 1. Fetch template
            template_res = db.table("onboarding_templates").select("*").eq("id", template_id).execute()
            if not template_res.data:
                raise ValueError("Template not found")
            template = template_res.data[0]
            
            # 2. Extract tasks_json
            tasks = template.get("tasks_json", [])
            tasks_to_insert = []
            
            # 3. Create task entries with due dates
            for task in tasks:
                due_days = task.get("due_days", 7)
                due_date = datetime.datetime.now() + datetime.timedelta(days=due_days)
                
                tasks_to_insert.append({
                    "employee_id": employee_id,
                    "title": task.get("title", "Untitled Task"),
                    "task_type": task.get("task_type", "Form"),
                    "status": "Pending",
                    "due_date": due_date.isoformat()
                })
            
            if tasks_to_insert:
                db.table("onboarding_tasks").insert(tasks_to_insert).execute()
                
            return {"status": "success", "tasks_created": len(tasks_to_insert)}
        except Exception as e:
            print(f"Failed to instantiate workflow: {str(e)}")
            raise e

    @staticmethod
    def notify_user(db, user_id: str, title: str, message: str, action_url: str = None):
        """Creates a notification for the user."""
        try:
            db.table("notifications").insert({
                "user_id": user_id,
                "title": title,
                "message": message,
                "action_url": action_url
            }).execute()
        except Exception as e:
            print(f"Failed to send notification: {str(e)}")
