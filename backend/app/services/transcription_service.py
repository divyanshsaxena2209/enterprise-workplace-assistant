import os
from openai import OpenAI
from app.core.config import settings
import io

openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

def transcribe_audio_file(file_bytes: bytes, filename: str) -> str:
    """
    Transcribe audio bytes using OpenAI's Whisper API.
    For production, large files should be chunked before calling the API.
    """
    try:
        # We write to a temporary file because the OpenAI API client expects a file-like object with a filename
        import tempfile
        ext = filename.split('.')[-1]
        
        with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp_file:
            tmp_file.write(file_bytes)
            tmp_path = tmp_file.name
            
        with open(tmp_path, "rb") as audio_file:
            transcript = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text" # can be 'verbose_json' for timestamps
            )
            
        os.remove(tmp_path)
        return transcript
    except Exception as e:
        raise RuntimeError(f"Transcription failed: {str(e)}")
