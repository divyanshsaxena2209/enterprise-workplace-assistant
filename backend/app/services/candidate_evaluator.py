"""
Candidate Evaluator Service
Acts as a senior recruiter and hiring manager to evaluate a parsed resume against a specific job description using Gemini structured outputs.
"""

import logging
from typing import List
from pydantic import BaseModel, Field
from google import genai

from app.core.config import settings
from app.core.exceptions import ServiceUnavailableError
from app.schemas.resume import ParsedResumeData
from app.schemas.job import JobResponse
from app.schemas.candidate_score import RecommendationLevel

logger = logging.getLogger(__name__)

if not settings.GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY is not set. AI evaluation will fail.")

class EvaluationResult(BaseModel):
    """Structured output for the AI evaluation."""
    match_percentage: int = Field(ge=0, le=100, description="Score from 0 to 100 based on Skill, Experience, Education, and Responsibility match.")
    ai_summary: str = Field(description="A 150-250 word summary explaining why the candidate matches, what requirements are satisfied or missing, and overall hiring suitability.")
    strengths: List[str] = Field(description="Specific strengths of the candidate directly relevant to the job (e.g. 'Strong FastAPI experience'). Avoid generic statements.")
    weaknesses: List[str] = Field(description="Specific gaps or weaknesses in the candidate's profile relative to the job (e.g. 'No AWS experience'). Avoid vague criticism.")
    recommendation: RecommendationLevel = Field(description="Final recommendation category.")

class CandidateEvaluatorService:
    """Service to evaluate candidate parsed resume against job requirements using Gemini."""

    def evaluate_against_job(self, job: JobResponse, parsed_resume: ParsedResumeData) -> EvaluationResult:
        """
        Evaluate the candidate against the provided job description and requirements.
        """
        if not settings.GEMINI_API_KEY:
            raise ServiceUnavailableError("AI configuration is missing. Cannot evaluate candidate.")

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

        EVALUATION GUIDELINES:
        1. Be RUTHLESSLY STRICT, OBJECTIVE, and PRACTICAL. Do not inflate scores out of politeness.
        2. If the candidate's resume shows NO relevant skills for the job, their match_percentage MUST BE BELOW 20%. Do NOT award baseline points just for having a resume.
        3. If the candidate lacks core skills, required experience, or shows no direct evidence of fulfilling the responsibilities, heavily penalize the match_percentage.
        4. Do not invent or assume skills that are not explicitly stated.
        5. If the candidate is a complete beginner or "noob" applying for a role requiring specific skills they don't possess, give a very low score and state clearly they are too junior.
        6. The ai_summary must be highly stringent, grounded in reality, and practical. DO NOT use generic, people-pleasing language or find "good things" to say if there are none. Clearly state if the candidate is unqualified or if their experience is completely irrelevant.
        7. Identify concrete strengths, but if there are no relevant strengths for the role, state EXACTLY "No relevant strengths listed."
        8. Identify glaring weaknesses and gaps bluntly and practically.
        9. The ai_summary should be between 150-250 words.
        """

        department_name = job.department or "Executive"
        system_prompt = (
            f"You are an elite, highly critical Senior {department_name} Recruiter and Hiring Manager. "
            "Your task is to protect the company's time by ruthlessly screening candidates against specific job requirements. "
            "You must provide realistic, stringent, and practical evaluations. Do not be overly polite or people-pleasing. "
            "If a candidate lacks required skills, give them a low score and plainly state they are unqualified, while remaining professional and objective."
        )

        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            
            prompt = f"System Instruction: {system_prompt}\n\n{prompt_content}"
            
            response = client.models.generate_content(
                model="gemma-4-31b-it",
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=EvaluationResult,
                    temperature=0.0,
                )
            )
            
            eval_data = response.parsed
            
            if not eval_data:
                raise ServiceUnavailableError("AI model returned an empty evaluation response.")
                
            return eval_data
            
        except Exception as exc:
            logger.error("Unexpected error during candidate evaluation: %s", exc)
            raise ServiceUnavailableError("Failed to evaluate the candidate.") from exc
