import os
import chromadb
from google import genai
from pydantic import BaseModel
from app.core.config import settings

class AIService:
    def __init__(self):
        # Gemini Setup
        self.genai_client = genai.Client(api_key=settings.GEMINI_API_KEY)
        
        # ChromaDB Setup
        self.chroma_client = chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)
        
        # Ensures collection exists
        self.document_collection = self.chroma_client.get_or_create_collection(name="company_documents")

    def generate_completion(self, system_prompt: str, user_prompt: str, model: str = "gemma-4-31b-it"):
        """Wrapper for basic Chat Completions using Gemini."""
        prompt = f"System: {system_prompt}\n\nUser: {user_prompt}"
        response = self.genai_client.models.generate_content(
            model=model,
            contents=prompt
        )
        return response.text

    def add_to_knowledge_base(self, doc_id: str, text: str, metadata: dict = None):
        """Add text document to ChromaDB for RAG."""
        self.document_collection.add(
            documents=[text],
            metadatas=[metadata or {}],
            ids=[doc_id]
        )

    def query_knowledge_base(self, query: str, n_results: int = 3):
        """Query ChromaDB for RAG retrieval."""
        results = self.document_collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results

    def evaluate_candidate(self, resume_data: dict, job_description: str, job_requirements: list[str]):
        """Evaluate a candidate's parsed resume against the job description using Gemini Structured Output."""
        from app.schemas.ats import CandidateScoreBase
        
        system_prompt = (
            "You are an expert technical recruiter and AI hiring assistant. "
            "Your task is to evaluate the provided candidate resume data against the job description and requirements. "
            "Return the evaluation strictly adhering to the JSON schema."
        )
        
        user_prompt = f"Job Description:\n{job_description}\n\nJob Requirements:\n{job_requirements}\n\nCandidate Resume Data:\n{resume_data}"
        
        prompt = f"System Instruction: {system_prompt}\n\n{user_prompt}"
        
        response = self.genai_client.models.generate_content(
            model="gemma-4-31b-it",
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CandidateScoreBase,
            ),
        )
        
        # Gemini returns structured output in response.parsed if a Pydantic schema is passed
        return response.parsed

ai_service = AIService()
