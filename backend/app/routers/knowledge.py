from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import List, Optional
from pydantic import BaseModel
from app.db.supabase import get_db
from app.services.document_parser import extract_document_text
from app.services.rag_service import RAGService
import uuid

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])

class SearchRequest(BaseModel):
    query: str
    department: Optional[str] = None

class ChatRequest(BaseModel):
    query: str
    department: Optional[str] = None
    chat_id: Optional[str] = None

@router.post("/documents")
async def upload_document(
    file: UploadFile = File(...),
    department_tag: str = Form(None),
    db=Depends(get_db)
):
    try:
        # 1. Read file
        file_bytes = await file.read()
        
        # 2. Store document metadata in Postgres (Processing state)
        doc_data = {
            "title": file.filename,
            "filename": file.filename,
            "file_url": f"/mock/storage/{file.filename}", # In real app, upload to Supabase Storage first
            "department_tag": department_tag,
            "status": "Processing"
        }
        res = db.table("documents").insert(doc_data).execute()
        document_id = res.data[0]["id"]
        
        # 3. Extract text
        text = extract_document_text(file_bytes, file.filename)
        
        # 4. Ingest into ChromaDB via RAGService
        metadata = {"department": department_tag, "filename": file.filename} if department_tag else {"filename": file.filename}
        chunk_ids = RAGService.ingest_document(document_id, text, metadata)
        
        # 5. Update Postgres state to Active
        db.table("documents").update({"status": "Active"}).eq("id", document_id).execute()
        
        # 6. Log chunks in DB (simplified)
        for i, cid in enumerate(chunk_ids):
            db.table("document_chunks").insert({
                "document_id": document_id,
                "chunk_index": i,
                "vector_id": cid
            }).execute()

        return {"status": "success", "document_id": document_id, "chunks_processed": len(chunk_ids)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search")
def semantic_search(req: SearchRequest, db=Depends(get_db)):
    try:
        results = RAGService.semantic_search(req.query, req.department)
        
        # Log retrieval
        db.table("retrieval_logs").insert({
            "query": req.query,
            "chunks_retrieved": len(results),
            "latency_ms": 0 # Would calculate actual latency
        }).execute()
        
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
def chat_with_knowledge(req: ChatRequest, db=Depends(get_db)):
    try:
        # 1. Retrieve context
        retrieved_chunks = RAGService.semantic_search(req.query, req.department, top_k=3)
        
        # 2. Generate response using RAG
        response_text = RAGService.generate_rag_response(req.query, retrieved_chunks)
        
        # 3. Handle chat session (mock logic for brevity)
        chat_id = req.chat_id or str(uuid.uuid4())
        
        # If new, create chat entry (omitted DB call for brevity)
        
        # 4. Save messages to db
        db.table("chat_messages").insert([
            {"chat_id": chat_id, "role": "user", "content": req.query},
            {"chat_id": chat_id, "role": "assistant", "content": response_text}
        ]).execute()
        
        return {
            "chat_id": chat_id,
            "response": response_text,
            "sources": retrieved_chunks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
