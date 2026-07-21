import uuid
import chromadb
from typing import List, Dict, Any
from app.core.config import settings
from app.services.embedding_service import generate_embeddings, generate_embedding
from app.services.chunking_service import chunk_text
from google import genai

genai_client = genai.Client(api_key=settings.GEMINI_API_KEY)
chroma_client = chromadb.PersistentClient(path="./chroma_db")

knowledge_collection = chroma_client.get_or_create_collection(
    name="enterprise_knowledge"
)

class RAGService:
    @staticmethod
    def ingest_document(document_id: str, text: str, metadata: Dict[str, Any]):
        """Chunks text, generates embeddings, and stores them in ChromaDB with metadata."""
        chunks = chunk_text(text)
        if not chunks:
            return []

        embeddings = generate_embeddings(chunks)
        
        ids = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{document_id}_chunk_{i}"
            ids.append(chunk_id)
            
            chunk_meta = metadata.copy()
            chunk_meta.update({
                "document_id": document_id,
                "chunk_index": i,
                "text_snippet": chunk[:200] # Store snippet for preview
            })
            metadatas.append(chunk_meta)
            
        knowledge_collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas
        )
        return ids

    @staticmethod
    def semantic_search(query: str, department_filter: str = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieves top_k chunks matching the query. Applies department filtering if provided."""
        query_embedding = generate_embedding(query)
        
        where_clause = {}
        if department_filter:
            where_clause["department"] = department_filter
            
        results = knowledge_collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_clause if where_clause else None
        )
        
        retrieved = []
        if results and results['ids'] and len(results['ids']) > 0:
            for i in range(len(results['ids'][0])):
                retrieved.append({
                    "id": results['ids'][0][i],
                    "document": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i] if 'distances' in results and results['distances'] else None
                })
        return retrieved

    @staticmethod
    def generate_rag_response(query: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
        """Injects retrieved chunks into Gemini to generate a factual response."""
        context_texts = []
        for i, chunk in enumerate(retrieved_chunks):
            doc_id = chunk["metadata"].get("document_id", "Unknown")
            context_texts.append(f"--- Document Source [{i+1}] (DocID: {doc_id}) ---\n{chunk['document']}\n")
            
        context_block = "\n".join(context_texts)
        
        system_prompt = (
            "You are a helpful and highly accurate Enterprise Knowledge AI Assistant. "
            "You have been provided with contextual snippets from company documents. "
            "Your task is to answer the user's question STRICTLY using the provided context. "
            "If the context does not contain the answer, reply stating that you do not have enough information. "
            "Do NOT hallucinate or use outside knowledge. Cite your sources using the Document Source number."
        )
        
        prompt = f"System Instruction: {system_prompt}\n\nContext:\n{context_block}\n\nQuestion:\n{query}"
        
        response = genai_client.models.generate_content(
            model="gemma-4-31b-it",
            contents=prompt
        )
        return response.text
