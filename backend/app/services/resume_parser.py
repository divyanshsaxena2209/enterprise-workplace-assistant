"""
Resume Parser Service
Extracts text from PDF/DOCX files and uses OpenAI to structure the raw text into JSON.
"""

import io
import logging
from typing import Optional
import PyPDF2
import docx2txt
import openai

from app.core.config import settings
from app.core.exceptions import BadRequestError, ServiceUnavailableError
from app.schemas.resume import ParsedResumeData

logger = logging.getLogger(__name__)

# Initialize OpenAI client
if settings.OPENAI_API_KEY:
    openai.api_key = settings.OPENAI_API_KEY
else:
    logger.warning("OPENAI_API_KEY is not set. AI parsing will fail.")


class ResumeParserService:
    """Service to parse raw resumes into structured data."""

    def extract_text(self, file_bytes: bytes, filename: str) -> str:
        """
        Extract raw text from PDF or DOCX file bytes.
        Raises BadRequestError if the file type is unsupported or corrupted.
        """
        file_ext = filename.lower().split('.')[-1]
        text = ""

        try:
            if file_ext == "pdf":
                reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
            elif file_ext in ["doc", "docx"]:
                text = docx2txt.process(io.BytesIO(file_bytes))
            else:
                raise BadRequestError(f"Unsupported file format: {file_ext}. Only PDF and DOCX are allowed.")
        except BadRequestError:
            raise
        except Exception as exc:
            logger.error("Failed to extract text from %s: %s", filename, exc)
            raise BadRequestError("Could not read the file. The file may be corrupted.") from exc

        if not text.strip():
            raise BadRequestError("No readable text found in the document.")

        return text.strip()

    def parse_with_ai(self, raw_text: str) -> ParsedResumeData:
        """
        Send raw resume text to OpenAI to parse into structured JSON.
        Uses GPT-4o structured outputs feature.
        """
        if not settings.OPENAI_API_KEY:
            raise ServiceUnavailableError("OpenAI API key is missing. Cannot parse resume.")

        try:
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            
            # Use structured outputs via response_format
            response = client.beta.chat.completions.parse(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert HR assistant. Extract the candidate's information from the provided resume text into the required structured format. Be precise and thorough."},
                    {"role": "user", "content": raw_text}
                ],
                response_format=ParsedResumeData,
                temperature=0.0,
            )
            
            parsed_data = response.choices[0].message.parsed
            
            if not parsed_data:
                raise ServiceUnavailableError("AI model returned an empty response.")
                
            return parsed_data
            
        except openai.OpenAIError as exc:
            logger.error("OpenAI API error during resume parsing: %s", exc)
            raise ServiceUnavailableError("AI parsing service is currently unavailable.") from exc
        except Exception as exc:
            logger.error("Unexpected error during resume AI parsing: %s", exc)
            raise ServiceUnavailableError("Failed to structure the resume data.") from exc
