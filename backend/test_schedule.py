import asyncio
from uuid import UUID
from supabase import create_client
from app.core.config import settings
from app.repositories.application_repository import ApplicationRepository
from app.services.application_service import ApplicationService
from app.schemas.interview import InterviewCreate
from datetime import datetime, timezone

client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
repo = ApplicationRepository(client)
svc = ApplicationService(repo, client)

interview_data = InterviewCreate(
    scheduled_at=datetime.now(timezone.utc),
    meeting_link="https://meet.google.com/test",
    management_notes="test"
)

# Use the application ID from the user's current route
app_id = UUID("7c0a40be-05ff-4840-9c09-700d1f2cb9cc")
# Use a random UUID for user_id
user_id = UUID("00000000-0000-0000-0000-000000000000")

try:
    res = svc.schedule_interview(app_id, interview_data, user_id)
    print("SUCCESS:", res)
except Exception as e:
    print("ERROR:", e)
