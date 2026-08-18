from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class ChatMessage(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    sources: List[Any] = []
    created_at: datetime

class ChatSession(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime

class ChatSessionCreate(BaseModel):
    title: Optional[str] = "New Chat"

class ChatSessionUpdate(BaseModel):
    title: str
