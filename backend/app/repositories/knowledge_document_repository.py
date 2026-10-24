"""Backend-only persistence for knowledge-document metadata."""

from typing import Any

from app.core.exceptions import DatabaseError

_TABLE = "knowledge_documents"
_PUBLIC_COLUMNS = (
    "id, filename, storage_provider, file_key, file_url, pages, chunks, "
    "uploaded_by, created_at, updated_at"
)


class KnowledgeDocumentRepository:
    """Access the registry through the trusted service-role Supabase client."""

    def __init__(self, client: Any) -> None:
        self._db = client

    def list_documents(self) -> list[dict]:
        try:
            response = (
                self._db.table(_TABLE)
                .select(_PUBLIC_COLUMNS)
                .order("created_at", desc=True)
                .execute()
            )
            return response.data or []
        except Exception as exc:
            raise DatabaseError("Failed to list knowledge documents.") from exc

    def create_document(self, values: dict) -> dict:
        try:
            response = (
                self._db.table(_TABLE)
                .insert(values)
                .select(_PUBLIC_COLUMNS)
                .execute()
            )
        except Exception as exc:
            raise DatabaseError("Failed to register the knowledge document.") from exc
        if not response.data:
            raise DatabaseError("Knowledge-document registration returned no row.")
        return response.data[0]

    def get_by_id(self, document_id: str) -> dict | None:
        try:
            response = (
                self._db.table(_TABLE)
                .select("*")
                .eq("id", document_id)
                .limit(1)
                .execute()
            )
        except Exception as exc:
            raise DatabaseError("Failed to load the knowledge document.") from exc
        return response.data[0] if response.data else None

    def delete_by_id(self, document_id: str) -> bool:
        try:
            response = (
                self._db.table(_TABLE)
                .delete()
                .eq("id", document_id)
                .select("id")
                .execute()
            )
        except Exception as exc:
            raise DatabaseError("Failed to remove the knowledge-document record.") from exc
        return bool(response.data)
