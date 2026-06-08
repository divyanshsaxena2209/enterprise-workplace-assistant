import os
import chromadb
from openai import OpenAI
from app.core.config import settings

class AIService:
    def __init__(self):
        # OpenAI Setup
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # ChromaDB Setup
        self.chroma_client = chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)
        
        # Ensures collection exists
        self.document_collection = self.chroma_client.get_or_create_collection(name="company_documents")

    def generate_completion(self, system_prompt: str, user_prompt: str, model: str = "gpt-4o"):
        """Wrapper for basic Chat Completions."""
        response = self.openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        return response.choices[0].message.content


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
        """Evaluate a candidate's parsed resume against the job description."""
        from app.schemas.ats import CandidateScoreBase
        system_prompt = (
            "You are an expert technical recruiter and AI hiring assistant. "
            "Your task is to evaluate the provided candidate resume data against the job description and requirements. "
            "Return the evaluation strictly adhering to the JSON schema provided."
        )
        
        user_prompt = f"Job Description:\n{job_description}\n\nJob Requirements:\n{job_requirements}\n\nCandidate Resume Data:\n{resume_data}"
        
        response = self.openai_client.beta.chat.completions.parse(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format=CandidateScoreBase
        )
        return response.choices[0].message.parsed

ai_service = AIService()
