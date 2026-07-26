import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from pydantic import BaseModel
from app.services.knowledge_rag import process_and_store_document, retrieve_and_answer

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class QueryRequest(BaseModel):
    question: str

@router.post("/upload")
async def upload_document(request: Request, file: UploadFile = File(...)):
    
    
    
    ALLOWED_TYPES = [
        "application/pdf", 
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are allowed.")

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    import uuid
    from app.db.supabase import get_supabase_client
    
    file_bytes = await file.read()
    
    
    with open(file_path, "wb") as buffer:
        buffer.write(file_bytes)

    try:
        
        result = process_and_store_document(file_path)
    except Exception as e:
        
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))
        
    
    try:
        client = get_supabase_client()
        unique_filename = f"knowledge_{uuid.uuid4()}_{file.filename.replace(' ', '_')}"
        client.storage.from_("resumes").upload(
            path=unique_filename,
            file=file_bytes,
            file_options={"content-type": file.content_type}
        )
        file_url = client.storage.from_("resumes").get_public_url(unique_filename)
    except Exception as exc:
        print(f"Failed to upload to storage: {exc}")
        file_url = None

    
    if os.path.exists(file_path):
        os.remove(file_path)

    return {
        "success": True,
        "filename": file.filename,
        "pages": result.get("pages", 0),
        "chunks": result.get("chunks", 0),
        "file_url": file_url,
        "message": "Document uploaded and indexed successfully."
    }

@router.post("/query")
async def query_documents(request: Request, query: QueryRequest):
    if not query.question or not query.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
        
    try:
        result = retrieve_and_answer(query.question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class DeleteDocumentRequest(BaseModel):
    filename: str
    file_url: str | None = None

@router.delete("/document")
async def delete_document_endpoint(request: Request, body: DeleteDocumentRequest):
    try:
        from app.services.knowledge_rag import delete_document
        deleted_chunks = delete_document(body.filename)
        
        
        if body.file_url:
            from app.db.supabase import get_supabase_client
            
            try:
                storage_filename = body.file_url.split('/')[-1]
                client = get_supabase_client()
                client.storage.from_("resumes").remove([storage_filename])
            except Exception as e:
                print(f"Failed to remove from storage: {e}")
                
        return {"success": True, "deleted_chunks": deleted_chunks, "message": f"Document '{body.filename}' deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
