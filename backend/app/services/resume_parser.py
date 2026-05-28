import io
import json
import PyPDF2
import docx2txt
from openai import OpenAI
from pydantic import BaseModel
from typing import List, Optional
from app.core.config import settings

openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

class StructuredResume(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: List[str] = []
    experience: List[dict] = []
    education: List[dict] = []
    certifications: List[str] = []
    projects: List[str] = []
    previous_companies: List[str] = []

def extract_raw_text(file_bytes: bytes, filename: str) -> str:
    """Extract raw text from PDF or DOCX."""
    text = ""
    if filename.lower().endswith(".pdf"):
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    elif filename.lower().endswith(".docx"):
        text = docx2txt.process(io.BytesIO(file_bytes))
    else:
        raise ValueError("Unsupported file format. Please upload PDF or DOCX.")
    return text

def parse_resume_with_ai(raw_text: str) -> StructuredResume:
    """Use GPT-4o to extract structured JSON from raw resume text."""
    system_prompt = (
        "You are an expert HR AI assistant. "
        "Extract the candidate's name, email, phone, skills, experience, education, "
        "certifications, projects, and previous_companies from the following resume text. "
        "Return the output STRICTLY as a JSON object matching the requested schema."
    )
    
    response = openai_client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": raw_text}
        ],
        response_format=StructuredResume
    )
    
    return response.choices[0].message.parsed
