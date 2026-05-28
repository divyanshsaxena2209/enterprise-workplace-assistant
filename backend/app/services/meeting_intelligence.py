from pydantic import BaseModel, Field
from typing import List, Optional
from openai import OpenAI
from app.core.config import settings

openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

class MeetingTask(BaseModel):
    title: str
    description: str
    assigned_to_name: Optional[str] = None
    priority: str = Field(description="Low, Medium, High, Critical")
    deadline: Optional[str] = None

class MeetingSummary(BaseModel):
    executive_summary: str
    decisions_made: List[str]
    discussion_points: List[str]
    action_items: List[MeetingTask]

def analyze_meeting(transcript: str) -> MeetingSummary:
    """Use GPT-4o structured outputs to extract insights and tasks from a transcript."""
    system_prompt = (
        "You are an expert AI Meeting Assistant. Analyze the provided meeting transcript. "
        "Extract a concise executive summary, the key decisions made, the main discussion points, "
        "and any action items (tasks). If a task has an assignee or deadline mentioned, include it. "
        "Return the output STRICTLY adhering to the provided JSON schema."
    )
    
    response = openai_client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Transcript:\n{transcript}"}
        ],
        response_format=MeetingSummary
    )
    
    return response.choices[0].message.parsed
