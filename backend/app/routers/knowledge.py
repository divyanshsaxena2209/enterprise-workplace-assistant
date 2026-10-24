"""Authenticated company knowledge base routes."""

import asyncio
import functools
import logging
import os
import tempfile
import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.db.supabase import get_supabase_client
from app.core.enums import UserRole
from app.dependencies.auth import require_management, require_management_or_employee
from app.repositories.knowledge_document_repository import KnowledgeDocumentRepository
from app.schemas.knowledge_chat import ChatSessionCreate, ChatSessionUpdate
from app.schemas.profile import ProfileResponse
from app.services import knowledge_chat_service
from app.services.knowledge_scope import document_scope_visible, normalize_department_scope

router = APIRouter()
UPLOAD_DIR = tempfile.gettempdir()
MAX_FILE_SIZE = 10 * 1024 * 1024
_ALLOWED_TYPES = {
    "pdf": {"application/pdf", "application/octet-stream"},
    "docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/octet-stream",
    },
}
logger = logging.getLogger(__name__)


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=8000)
    session_id: str | None = None


class DeleteDocumentRequest(BaseModel):
    # document_id selects a trusted database record. Legacy localStorage documents
    # have no registry ID and continue through the strict key-prefix fallback.
    document_id: UUID | None = None
    filename: str | None = None
    file_url: str | None = None
    file_key: str | None = None
    storage_provider: str | None = None


def _document_repository() -> KnowledgeDocumentRepository:
    return KnowledgeDocumentRepository(get_supabase_client())


def _public_document(row: dict) -> dict:
    """Avoid returning the internal Qdrant source path to the browser."""
    return {
        key: row.get(key)
        for key in (
            "id", "filename", "storage_provider", "file_key", "file_url", "department_scope",
            "pages", "chunks", "uploaded_by", "created_at", "updated_at",
        )
    }


def _remove_temp_file(path: str) -> None:
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        logger.warning("Could not remove a temporary knowledge-upload file.")


@router.get("/documents")
def list_knowledge_documents(
    current_user: ProfileResponse = Depends(require_management_or_employee),
):
    """Return only company-wide and department-matched records to employees."""
    try:
        rows = _document_repository().list_documents()
        is_management = current_user.role in UserRole.management_roles()
        return [
            row for row in rows
            if document_scope_visible(
                row.get("department_scope"),
                current_user.department,
                is_management=is_management,
            )
        ]
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail="Unable to load the knowledge-document list."
        ) from exc


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: ProfileResponse = Depends(require_management),
    department_scope: str = Form(default="ALL", max_length=100),
):
    original_name = (file.filename or "").replace("\\", "/")
    safe_filename = os.path.basename(original_name)
    if not safe_filename or safe_filename in {".", ".."}:
        raise HTTPException(status_code=400, detail="A valid filename is required.")

    extension = safe_filename.rsplit(".", 1)[-1].lower() if "." in safe_filename else ""
    if extension not in _ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are allowed.")
    if file.content_type not in _ALLOWED_TYPES[extension]:
        raise HTTPException(status_code=400, detail="The file type does not match its extension.")

    file_bytes = await file.read(MAX_FILE_SIZE + 1)
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Documents must be 10 MB or smaller.")
    if not file_bytes:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    scope_label = normalize_department_scope(department_scope)
    if len(scope_label) > 100:
        raise HTTPException(status_code=422, detail="Department scope must be 100 characters or fewer.")

    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{safe_filename}")
    stored = None
    indexing_attempted = False
    registered = False
    try:
        with open(file_path, "wb") as output:
            output.write(file_bytes)

        # Store bytes first, so storage failures never create RAG-only content.
        from app.services.object_storage import upload_knowledge_document
        stored = upload_knowledge_document(
            safe_filename,
            file_bytes,
            file.content_type or "application/octet-stream",
            prefix="knowledge",
        )

        indexing_attempted = True
        from app.services.knowledge_rag import process_and_store_document
        loop = asyncio.get_running_loop()
        index_result = await loop.run_in_executor(
            None,
            functools.partial(
                process_and_store_document,
                file_path,
                department_scope=scope_label,
            ),
        )

        provider = str(stored["storage_provider"])
        file_key = str(stored["file_key"])
        # Presigned S3 URLs expire and are bearer credentials; store a stable key only.
        durable_url = stored.get("file_url") if provider == "supabase" else None
        row = _document_repository().create_document(
            {
                "filename": safe_filename,
                "storage_provider": provider,
                "file_key": file_key,
                "file_url": durable_url,
                "department_scope": scope_label,
                "index_source": file_path,
                "pages": int(index_result.get("pages", 0)),
                "chunks": int(index_result.get("chunks", 0)),
                "uploaded_by": str(current_user.id),
            }
        )
        registered = True
        return {
            **_public_document(row),
            "success": True,
            "message": "Document uploaded and indexed successfully.",
        }
    except HTTPException:
        raise
    except Exception as exc:
        # Roll back partial cross-service writes; log exception classes only.
        if indexing_attempted:
            try:
                from app.services.knowledge_rag import delete_document
                await asyncio.get_running_loop().run_in_executor(
                    None, functools.partial(delete_document, file_path, exact_source=True)
                )
            except Exception as cleanup_exc:
                logger.warning("Knowledge-index cleanup failed (exception_type=%s).", type(cleanup_exc).__name__)
        if stored and not registered:
            try:
                from app.services.object_storage import delete_knowledge_document_object
                delete_knowledge_document_object(
                    stored.get("storage_provider"), stored.get("file_key"), stored.get("file_url")
                )
            except Exception as cleanup_exc:
                logger.warning("Knowledge-object cleanup failed (exception_type=%s).", type(cleanup_exc).__name__)
        logger.error("Knowledge upload failed (exception_type=%s).", type(exc).__name__)
        raise HTTPException(
            status_code=500,
            detail="The document could not be stored, indexed, and registered.",
        ) from exc
    finally:
        _remove_temp_file(file_path)
        try:
            await file.close()
        except Exception:
            pass


@router.get("/sessions")
def get_sessions(current_user: ProfileResponse = Depends(require_management_or_employee)):
    try:
        return knowledge_chat_service.get_user_sessions(str(current_user.id))
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to load chat sessions.") from exc


@router.post("/sessions")
def create_session(body: ChatSessionCreate, current_user: ProfileResponse = Depends(require_management_or_employee)):
    try:
        return knowledge_chat_service.create_session(str(current_user.id), body.title)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unable to create the chat session.") from exc


@router.get("/sessions/{session_id}/messages")
def get_session_messages(session_id: str, current_user: ProfileResponse = Depends(require_management_or_employee)):
    try:
        return knowledge_chat_service.get_session_messages(session_id, str(current_user.id))
    except Exception as exc:
        if "not found" in str(exc).lower() or "unauthorized" in str(exc).lower():
            raise HTTPException(status_code=404, detail="Chat session not found.") from exc
        raise HTTPException(status_code=500, detail="Unable to load chat messages.") from exc


@router.put("/sessions/{session_id}")
def rename_session(session_id: str, body: ChatSessionUpdate, current_user: ProfileResponse = Depends(require_management_or_employee)):
    try:
        knowledge_chat_service.rename_session(session_id, str(current_user.id), body.title)
        return {"success": True, "message": "Session renamed successfully"}
    except Exception as exc:
        if "not found" in str(exc).lower() or "unauthorized" in str(exc).lower():
            raise HTTPException(status_code=404, detail="Chat session not found.") from exc
        raise HTTPException(status_code=500, detail="Unable to rename chat session.") from exc


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str, current_user: ProfileResponse = Depends(require_management_or_employee)):
    try:
        return knowledge_chat_service.delete_session(session_id, str(current_user.id))
    except Exception as exc:
        if "not found" in str(exc).lower() or "unauthorized" in str(exc).lower():
            raise HTTPException(status_code=404, detail="Chat session not found.") from exc
        raise HTTPException(status_code=500, detail="Unable to delete chat session.") from exc


@router.post("/query")
def query_documents(query: QueryRequest, current_user: ProfileResponse = Depends(require_management_or_employee)):
    if not query.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        chat_history = []
        if query.session_id:
            # The service-role client bypasses RLS, so ownership must be checked
            # explicitly before any message write or model invocation.
            try:
                history_rows = knowledge_chat_service.get_session_messages(
                    query.session_id, str(current_user.id)
                )
            except Exception as exc:
                message = str(exc).lower()
                if "not found" in message or "unauthorized" in message:
                    raise HTTPException(status_code=404, detail="Chat session not found.") from exc
                raise HTTPException(status_code=500, detail="Unable to load chat history.") from exc

            chat_history = [{"role": row["role"], "content": row["content"]} for row in history_rows]
            knowledge_chat_service.add_message(query.session_id, "user", query.question)

        from app.services.knowledge_rag import retrieve_and_answer
        is_management = current_user.role in UserRole.management_roles()
        department_scope = None if is_management else str(current_user.department or "")
        result = retrieve_and_answer(
            query.question,
            k=15,
            chat_history=chat_history,
            department_scope=department_scope,
        )

        if query.session_id:
            answer = result.get("answer", "") if isinstance(result, dict) else str(result)
            sources = result.get("sources", []) if isinstance(result, dict) else []
            knowledge_chat_service.add_message(query.session_id, "assistant", answer, sources)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Knowledge query failed (exception_type=%s).", type(exc).__name__)
        raise HTTPException(status_code=500, detail="Unable to process the knowledge query.") from exc


@router.get("/document/download")
def get_document_download_url(file_key: str, current_user: ProfileResponse = Depends(require_management_or_employee)):
    from app.services.object_storage import create_knowledge_document_download_url
    try:
        record = _document_repository().get_by_file_key(file_key)
        if not record or record.get("storage_provider") != "s3":
            raise HTTPException(status_code=404, detail="Knowledge document not found.")
        is_management = current_user.role in UserRole.management_roles()
        if not document_scope_visible(
            record.get("department_scope"),
            current_user.department,
            is_management=is_management,
        ):
            raise HTTPException(status_code=404, detail="Knowledge document not found.")
        return {"file_url": create_knowledge_document_download_url(file_key)}
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid knowledge document key.") from exc
    except Exception as exc:
        logger.error("Knowledge download URL failed (exception_type=%s).", type(exc).__name__)
        raise HTTPException(status_code=500, detail="Unable to create a temporary download URL.") from exc


@router.delete("/document")
async def delete_document_endpoint(
    body: DeleteDocumentRequest,
    current_user: ProfileResponse = Depends(require_management),
):
    repository = _document_repository()
    record = None
    if body.document_id is not None:
        try:
            record = repository.get_by_id(str(body.document_id))
        except Exception as exc:
            raise HTTPException(status_code=500, detail="Unable to load the knowledge-document record.") from exc
        if record is None:
            raise HTTPException(status_code=404, detail="Knowledge document not found.")
        filename = str(record["filename"])
        file_key = record.get("file_key")
        file_url = record.get("file_url")
        storage_provider = record.get("storage_provider")
        index_source = str(record["index_source"])
    else:
        supplied_name = (body.filename or "").replace("\\", "/")
        filename = os.path.basename(supplied_name)
        if not filename or filename in {".", ".."} or filename != supplied_name:
            raise HTTPException(status_code=400, detail="A valid document filename is required.")
        file_key = body.file_key
        file_url = body.file_url
        storage_provider = body.storage_provider
        index_source = None

    try:
        from app.services.knowledge_rag import delete_document
        loop = asyncio.get_running_loop()
        if index_source:
            deleted_chunks = await loop.run_in_executor(
                None, functools.partial(delete_document, index_source, exact_source=True)
            )
        else:
            deleted_chunks = await loop.run_in_executor(None, functools.partial(delete_document, filename))

        if file_key or file_url:
            from app.services.object_storage import delete_knowledge_document_object
            delete_knowledge_document_object(storage_provider, file_key, file_url)

        if record is not None and not repository.delete_by_id(str(body.document_id)):
            raise HTTPException(status_code=404, detail="Knowledge document not found.")
        return {"success": True, "deleted_chunks": deleted_chunks, "message": f"Document '{filename}' deleted successfully."}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Knowledge document deletion failed (exception_type=%s).", type(exc).__name__)
        raise HTTPException(status_code=500, detail="Unable to delete the knowledge document.") from exc
