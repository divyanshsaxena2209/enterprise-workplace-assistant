"""
Candidate Evaluator Service
Acts as a senior recruiter and hiring manager to evaluate a parsed resume against a specific job description using OpenAI structured outputs.
"""

import logging
from typing import List
from pydantic import BaseModel, Field
import openai

from app.core.config import settings
from app.core.exceptions import ServiceUnavailableError
from app.schemas.resume import ParsedResumeData
from app.schemas.job import JobResponse
from app.schemas.candidate_score import RecommendationLevel

logger = logging.getLogger(__name__)

# Initialize OpenAI client
if settings.OPENAI_API_KEY:
    openai.api_key = settings.OPENAI_API_KEY
else:
    logger.warning("OPENAI_API_KEY is not set. AI evaluation will fail.")

class EvaluationResult(BaseModel):
    """Structured output for the AI evaluation."""
    match_percentage: int = Field(ge=0, le=100, description="Score from 0 to 100 based on Skill, Experience, Education, and Responsibility match.")
    ai_summary: str = Field(description="A 150-250 word summary explaining why the candidate matches, what requirements are satisfied or missing, and overall hiring suitability.")
    strengths: List[str] = Field(description="Specific strengths of the candidate directly relevant to the job (e.g. 'Strong FastAPI experience'). Avoid generic statements.")
    weaknesses: List[str] = Field(description="Specific gaps or weaknesses in the candidate's profile relative to the job (e.g. 'No AWS experience'). Avoid vague criticism.")
    recommendation: RecommendationLevel = Field(description="Final recommendation category.")

class CandidateEvaluatorService:
    """Service to evaluate candidate parsed resume against job requirements using OpenAI."""

    def evaluate_against_job(self, job: JobResponse, parsed_resume: ParsedResumeData) -> EvaluationResult:
        """
        Evaluate the candidate against the provided job description and requirements.
        """
        if not settings.OPENAI_API_KEY:
            raise ServiceUnavailableError("OpenAI API key is missing. Cannot evaluate candidate.")

        job_context = f"""
        Job Title: {job.title}
        Department: {job.department}
        Experience Required: {job.experience_required}
        Description: {job.description}
        Requirements: {job.requirements}
        Responsibilities: {job.responsibilities}
        """

        resume_context = parsed_resume.model_dump_json(indent=2)

        prompt_content = f"""
        Please evaluate the following Candidate against the provided Job Description.

        --- JOB SPECIFICATION ---
        {job_context}

        --- CANDIDATE RESUME ---
        {resume_context}

        Evaluate strictly against the supplied job. Do not use external assumptions.
        The AI summary must be useful for recruiters, explaining:
        - Why the candidate matches
        - Which requirements are satisfied
        - Which requirements are missing
        - Overall hiring suitability
        Ensure the summary is between 150-250 words.
        """

        system_prompt = (
            "You are a Senior Technical Recruiter, Senior HR Specialist, and Hiring Manager. "
            "Your task is to critically evaluate candidates against specific job requirements. "
            "Be objective, thorough, decisive, and highly specific."
        )

        try:
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            
            response = client.beta.chat.completions.parse(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt_content}
                ],
                response_format=EvaluationResult,
                temperature=0.0,
            )
            
            eval_data = response.choices[0].message.parsed
            
            if not eval_data:
                raise ServiceUnavailableError("AI model returned an empty evaluation response.")
                
            return eval_data
            
        except openai.OpenAIError as exc:
            logger.error("OpenAI API error during candidate evaluation: %s", exc)
            raise ServiceUnavailableError("AI evaluation service is currently unavailable.") from exc
        except Exception as exc:
            logger.error("Unexpected error during candidate evaluation: %s", exc)
            raise ServiceUnavailableError("Failed to evaluate the candidate.") from exc
