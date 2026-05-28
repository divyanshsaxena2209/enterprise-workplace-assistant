import os
import tempfile
from openai import OpenAI
from pydantic import BaseModel, Field
from app.core.config import settings
from app.core.security import supabase_admin
from app.schemas.meetings import ActionItemExtract
from typing import List, Dict, Any, Optional

openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

class MeetingExtractionResult(BaseModel):
    summary: str = Field(..., description="Detailed markdown executive summary of the meeting, including key discussion topics and decisions in bullet points.")
    action_items: List[ActionItemExtract] = Field(default=[], description="List of action items extracted from the transcript.")

def transcribe_audio_bytes(file_bytes: bytes, file_path: str) -> str:
    """
    Saves file bytes to a temporary audio file and calls OpenAI Whisper API to transcribe.
    """
    ext = os.path.splitext(file_path)[1] or ".mp3"
    if ext.lower() not in [".mp3", ".wav", ".m4a", ".webm", ".ogg"]:
        ext = ".mp3" # Whisper-supported fallback

    # Create temporary file
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as temp_audio:
        temp_audio.write(file_bytes)
        temp_audio_path = temp_audio.name

    try:
        with open(temp_audio_path, "rb") as audio_file:
            transcription = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        return transcription.text
    except Exception as e:
        raise Exception(f"Whisper speech-to-text translation failed: {str(e)}")
    finally:
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)

def extract_meeting_insights(transcript_text: str) -> MeetingExtractionResult:
    """
    Invokes GPT-4o using Structured Outputs to generate a summary and extract tasks/action items.
    """
    prompt = f"""
    You are an expert Executive AI Meeting Assistant.
    Your task is to analyze the following meeting transcript.

    MEETING TRANSCRIPT:
    ---
    {transcript_text}
    ---

    Perform the following operations:
    1. Generate an executive-level summary of the meeting in beautiful, structured markdown format. Use bullet points for main topics discussed, agreements, and decisions.
    2. Extract all concrete action items, identifying who is responsible (assignee) and the deadline (date format YYYY-MM-DD if mentioned, or raw description like 'by next Friday', or leave as null/empty if unknown).
    """

    completion = openai_client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a professional corporate recorder. Extract meeting summaries and action items in structured format."},
            {"role": "user", "content": prompt}
        ],
        response_format=MeetingExtractionResult
    )

    return completion.choices[0].message.parsed

def match_assignee_profile(fallback_name: str) -> Optional[str]:
    """
    Queries the profiles table and tries to find a matching employee profile by name.
    Returns user UUID if found, otherwise None.
    """
    if not fallback_name or fallback_name.lower() in ["unassigned", "everyone", "team", "none", ""]:
        return None
    
    try:
        # Get all profiles
        res = supabase_admin.table("profiles").select("id", "full_name").execute()
        if not res.data:
            return None
        
        # Simple case-insensitive sub-string match
        fallback_name_lower = fallback_name.lower()
        for profile in res.data:
            full_name = profile.get("full_name", "")
            if not full_name:
                continue
            full_name_lower = full_name.lower()
            
            # If "John Doe" contains "John" or vice versa
            if fallback_name_lower in full_name_lower or full_name_lower in fallback_name_lower:
                return profile["id"]
        return None
    except Exception:
        return None
