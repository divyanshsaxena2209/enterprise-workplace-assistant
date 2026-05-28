from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ActionItemBase(BaseModel):
    task_description: str = Field(..., description="Details of the action item task")
    assignee_fallback_name: Optional[str] = Field(None, description="Raw text name of person assigned")
    deadline: Optional[str] = Field(None, description="Deadline or timeline of task, e.g. '2026-06-01' or 'None'")

class ActionItemExtract(ActionItemBase):
    pass

class ActionItemResponse(ActionItemBase):
    id: str
    meeting_id: str
    assignee_id: Optional[str] = None
    status: str
    created_at: str

    class Config:
        from_attributes = True

class MeetingResponse(BaseModel):
    id: str
    title: str
    meeting_date: str
    audio_file_path: Optional[str] = None
    transcript: Optional[str] = None
    summary: Optional[str] = None
    organized_by: str
    created_at: str

    class Config:
        from_attributes = True

class MeetingDetailResponse(MeetingResponse):
    action_items: List[ActionItemResponse] = []

class TranscribeRequest(BaseModel):
    audio_file_path: str = Field(..., description="Path to audio file in Supabase Storage")
    title: str = Field(..., description="Title of the meeting")
