import os
import tempfile
import uuid
from pathlib import Path
from urllib.parse import unquote, urlparse

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Request
from pydantic import BaseModel

from app.dependencies.auth import require_authenticated_user, require_management
from app.schemas.profile import ProfileResponse
from app.schemas.knowledge_chat import ChatSessionCreate, ChatSessionUpdate
from app.services.knowledge_rag import process_and_store_document, retrieve_and_answer
from app.services import knowledge_chat_service

router = APIRouter()
UPLOAD_DIR = tempfile.gettempdir()

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
MAX_KNOWLEDGE_FILE_SIZE = 20 * 1024 * 1024


class QueryRequest(BaseModel):
    question: str
    session_id: str | None = None


@router.post("/upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    current_user: ProfileResponse = Depends(require_management),
):
    """Management-only: upload and index an approved company knowledge document."""
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are allowed.")

    original_name = Path(file.filename or "").name
    suffix = Path(original_name).suffix.lower()
    if suffix not in {".pdf", ".docx"}:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are allowed.")

    file_bytes = await file.read(MAX_KNOWLEDGE_FILE_SIZE + 1)
    if not file_bytes:
        raise HTTPException(status_code=400, detail="The uploaded document is empty.")
    if len(file_bytes) > MAX_KNOWLEDGE_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Document exceeds the 20MB size limit.")

    temp_name = f"knowledge_{uuid.uuid4().hex}{suffix}"
    file_path = os.path.join(UPLOAD_DIR, temp_name)
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(file_bytes)

        import asyncio
        import functools
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, functools.partial(process_and_store_document, file_path)
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to process and index the document.") from exc
    finally:
        try:
            os.remove(file_path)
        except FileNotFoundError:
            pass

    # TODO(AWS migration): replace the legacy private-store boundary with the
    # dedicated S3 knowledge-document prefix and persist its stable object key.
    try:
        from app.db.supabase import get_supabase_client
        client = get_supabase_client()
        stored_name = f"knowledge_{uuid.uuid4()}_{original_name.replace(' ', '_')}"
        client.storage.from_("resumes").upload(
            path=stored_name,
            file=file_bytes,
            file_options={"content-type": file.content_type},
        )
        file_url = client.storage.from_("resumes").get_public_url(stored_name)
    except Exception as exc:
        # Avoid silently reporting a durable upload if storage did not persist.
        raise HTTPException(
            status_code=502,
            detail="The document was indexed but storage persistence failed.",
        ) from exc

    return {
        "success": True,
        "filename": original_name,
        "pages": result.get("pages", 0),
        "chunks": result.get("chunks", 0),
        "file_url": file_url,
        "message": "Document uploaded and indexed successfully.",
    }


@router.get("/sessions")
def get_sessions(current_user: ProfileResponse = Depends(require_authenticated_user)):
    try:
        return knowledge_chat_service.get_user_sessions(str(current_user.id))
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch chat sessions.") from exc


@router.post("/sessions")
def create_session(
    body: ChatSessionCreate,
    current_user: ProfileResponse = Depends(require_authenticated_user),
):
    try:
        return knowledge_chat_service.create_session(str(current_user.id), body.title)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to create chat session.") from exc


@router.get("/sessions/{session_id}/messages")
def get_session_messages(
    session_id: str,
    current_user: ProfileResponse = Depends(require_authenticated_user),
):
    try:
        return knowledge_chat_service.get_session_messages(session_id, str(current_user.id))
    except Exception as exc:
        if "not found" in str(exc).lower() or "unauthorized" in str(exc).lower():
            raise HTTPException(status_code=404, detail="Chat session not found.") from exc
        raise HTTPException(status_code=500, detail="Failed to fetch chat messages.") from exc


@router.put("/sessions/{session_id}")
def rename_session(
    session_id: str,
    body: ChatSessionUpdate,
    current_user: ProfileResponse = Depends(require_authenticated_user),
):
    try:
        knowledge_chat_service.rename_session(session_id, str(current_user.id), body.title)
        return {"success": True, "message": "Session renamed successfully"}
    except Exception as exc:
        if "not found" in str(exc).lower() or "unauthorized" in str(exc).lower():
            raise HTTPException(status_code=404, detail="Chat session not found.") from exc
        raise HTTPException(status_code=500, detail="Failed to rename chat session.") from exc


@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: str,
    current_user: ProfileResponse = Depends(require_authenticated_user),
):
    try:
        return knowledge_chat_service.delete_session(session_id, str(current_user.id))
    except Exception as exc:
        if "not found" in str(exc).lower() or "unauthorized" in str(exc).lower():
            raise HTTPException(status_code=404, detail="Chat session not found.") from exc
        raise HTTPException(status_code=500, detail="Failed to delete chat session.") from exc


@router.post("/query")
def query_documents(
    request: Request,
    query: QueryRequest,
    current_user: ProfileResponse = Depends(require_authenticated_user),
):
    if not query.question or not query.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        chat_history = []
        if query.session_id:
            history_rows = knowledge_chat_service.get_session_messages(
                query.session_id, str(current_user.id)
            )
            # Check ownership first; only then persist the user's message.
            knowledge_chat_service.add_message(query.session_id, "user", query.question)
            chat_history = [
                {"role": row["role"], "content": row["content"]} for row in history_rows
            ] + [{"role": "user", "content": query.question}]

        result = retrieve_and_answer(query.question, k=15, chat_history=chat_history)

        if query.session_id:
            answer = result.get("answer", "") if isinstance(result, dict) else str(result)
            sources = result.get("sources", []) if isinstance(result, dict) else []
            knowledge_chat_service.add_message(
                query.session_id, "assistant", answer, sources
            )
        return result
    except Exception as exc:
        if "not found" in str(exc).lower() or "unauthorized" in str(exc).lower():
            raise HTTPException(status_code=404, detail="Chat session not found.") from exc
        raise HTTPException(status_code=500, detail="Knowledge query failed. Please retry.") from exc


class DeleteDocumentRequest(BaseModel):
    filename: str
    file_url: str | None = None


@router.delete("/document")
async def delete_document_endpoint(
    request: Request,
    body: DeleteDocumentRequest,
    current_user: ProfileResponse = Depends(require_management),
):
    """Management-only document deletion; only accept a simple storage object key."""
    filename = Path(body.filename).name
    if not filename:
        raise HTTPException(status_code=400, detail="A document filename is required.")

    try:
        from app.services.knowledge_rag import delete_document
        import asyncio
        import functools
        loop = asyncio.get_running_loop()
        deleted_chunks = await loop.run_in_executor(
            None, functools.partial(delete_document, filename)
        )

        storage_deleted = False
        if body.file_url:
            parsed = urlparse(body.file_url)
            storage_filename = unquote(parsed.path.rsplit("/", 1)[-1])
            if (
                not storage_filename
                or storage_filename in {".", ".."}
                or "/" in storage_filename
                or "\\" in storage_filename
            ):
                raise HTTPException(status_code=400, detail="Invalid storage file reference.")

            from app.db.supabase import get_supabase_client
            client = get_supabase_client()
            client.storage.from_("resumes").remove([storage_filename])
            storage_deleted = True

        return {
            "success": True,
            "deleted_chunks": deleted_chunks,
            "storage_deleted": storage_deleted,
            "message": f"Document '{filename}' deletion processed.",
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to delete the knowledge document.") from exc
