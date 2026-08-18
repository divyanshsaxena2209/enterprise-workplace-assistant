import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from pydantic import BaseModel
from app.services.knowledge_rag import process_and_store_document, retrieve_and_answer

router = APIRouter()

import tempfile
UPLOAD_DIR = tempfile.gettempdir()

from fastapi import Depends
from app.dependencies.auth import require_authenticated_user
from app.schemas.profile import ProfileResponse
from app.schemas.knowledge_chat import ChatSessionCreate, ChatSessionUpdate
from app.services import knowledge_chat_service

class QueryRequest(BaseModel):
    question: str
    session_id: str | None = None

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
        import asyncio
        import functools
        loop = asyncio.get_event_loop()
        func = functools.partial(process_and_store_document, file_path)
        result = await loop.run_in_executor(None, func)
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

@router.get("/sessions")
def get_sessions(current_user: ProfileResponse = Depends(require_authenticated_user)):
    try:
        return knowledge_chat_service.get_user_sessions(str(current_user.id))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sessions")
def create_session(body: ChatSessionCreate, current_user: ProfileResponse = Depends(require_authenticated_user)):
    try:
        return knowledge_chat_service.create_session(str(current_user.id), body.title)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}/messages")
def get_session_messages(session_id: str, current_user: ProfileResponse = Depends(require_authenticated_user)):
    try:
        return knowledge_chat_service.get_session_messages(session_id, str(current_user.id))
    except Exception as e:
        if "not found" in str(e).lower() or "unauthorized" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/sessions/{session_id}")
def rename_session(session_id: str, body: ChatSessionUpdate, current_user: ProfileResponse = Depends(require_authenticated_user)):
    try:
        knowledge_chat_service.rename_session(session_id, str(current_user.id), body.title)
        return {"success": True, "message": "Session renamed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sessions/{session_id}")
def delete_session(session_id: str, current_user: ProfileResponse = Depends(require_authenticated_user)):
    try:
        return knowledge_chat_service.delete_session(session_id, str(current_user.id))
    except Exception as e:
        if "not found" in str(e).lower() or "unauthorized" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query")
def query_documents(
    request: Request, 
    query: QueryRequest,
    current_user: ProfileResponse = Depends(require_authenticated_user)
):
    print(f"[DEBUG] /query endpoint hit for user {current_user.id} with question: {query.question}")
    if not query.question or not query.question.strip():
        print("[DEBUG] /query aborted: Question is empty")
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
        
    try:
        chat_history = []
        if query.session_id:
            print(f"[DEBUG] Adding user message to DB for session {query.session_id}")
            knowledge_chat_service.add_message(query.session_id, "user", query.question)
            print(f"[DEBUG] Fetching session messages for chat history")
            history_rows = knowledge_chat_service.get_session_messages(query.session_id, str(current_user.id))
            chat_history = [{"role": row["role"], "content": row["content"]} for row in history_rows]
            print(f"[DEBUG] Chat history loaded. Length: {len(chat_history)}")

        print("[DEBUG] Calling retrieve_and_answer...")
        result = retrieve_and_answer(query.question, k=15, chat_history=chat_history)
        print("[DEBUG] retrieve_and_answer completed successfully")
        
        if query.session_id:
            print("[DEBUG] Adding assistant message to DB")
            answer = result.get("answer", "") if isinstance(result, dict) else str(result)
            sources = result.get("sources", []) if isinstance(result, dict) else []
            knowledge_chat_service.add_message(query.session_id, "assistant", answer, sources)
            print("[DEBUG] Assistant message saved successfully")
            
        print("[DEBUG] /query request fully completed")
        return result
    except Exception as e:
        print(f"[ERROR] /query endpoint failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

class DeleteDocumentRequest(BaseModel):
    filename: str
    file_url: str | None = None

@router.delete("/document")
async def delete_document_endpoint(request: Request, body: DeleteDocumentRequest):
    try:
        from app.services.knowledge_rag import delete_document
        import asyncio
        import functools
        loop = asyncio.get_event_loop()
        func = functools.partial(delete_document, body.filename)
        deleted_chunks = await loop.run_in_executor(None, func)
        
        
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
