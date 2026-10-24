from types import SimpleNamespace

from app.repositories.knowledge_document_repository import KnowledgeDocumentRepository


class FakeQuery:
    def __init__(self, client, table):
        self.client = client
        self.table = table
        self.operation = "select"
        self.values = None
        self.filters = []
        self.selected = None
        self.ordering = None
        self.row_limit = None

    def select(self, columns):
        self.selected = columns
        return self

    def insert(self, values):
        self.operation = "insert"
        self.values = values
        return self

    def delete(self):
        self.operation = "delete"
        return self

    def eq(self, column, value):
        self.filters.append((column, value))
        return self

    def order(self, column, desc=False):
        self.ordering = (column, desc)
        return self

    def limit(self, value):
        self.row_limit = value
        return self

    def execute(self):
        self.client.calls.append({
            "table": self.table,
            "operation": self.operation,
            "values": self.values,
            "filters": self.filters,
            "selected": self.selected,
            "ordering": self.ordering,
            "limit": self.row_limit,
        })
        if self.operation == "insert":
            row = {"id": "doc-1", **self.values}
            if self.selected and self.selected != "*":
                columns = [column.strip() for column in self.selected.split(",")]
                row = {column: row.get(column) for column in columns}
            return SimpleNamespace(data=[row])
        if self.operation == "delete":
            return SimpleNamespace(data=[{"id": "doc-1"}])
        return SimpleNamespace(data=self.client.rows)


class FakeClient:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.calls = []

    def table(self, name):
        return FakeQuery(self, name)


def test_registry_lists_metadata_and_keeps_vector_source_internal():
    client = FakeClient([{"id": "doc-1", "filename": "policy.pdf"}])
    repository = KnowledgeDocumentRepository(client)

    listed = repository.list_documents()
    created = repository.create_document({
        "filename": "policy.pdf",
        "storage_provider": "s3",
        "file_key": "knowledge/knowledge_123_policy.pdf",
        "file_url": None,
        "index_source": "/tmp/unique_policy.pdf",
        "pages": 4,
        "chunks": 2,
        "uploaded_by": "manager-1",
    })

    assert listed == [{"id": "doc-1", "filename": "policy.pdf"}]
    assert created["file_key"] == "knowledge/knowledge_123_policy.pdf"
    assert "index_source" not in created
    assert "index_source" not in client.calls[0]["selected"]
    assert client.calls[0]["table"] == "knowledge_documents"
    assert client.calls[0]["ordering"] == ("created_at", True)
    assert client.calls[1]["operation"] == "insert"
    assert client.calls[1]["values"]["index_source"] == "/tmp/unique_policy.pdf"


def test_registry_lookup_and_delete_use_record_id():
    client = FakeClient([{"id": "doc-1", "index_source": "/tmp/unique_policy.pdf"}])
    repository = KnowledgeDocumentRepository(client)

    found = repository.get_by_id("doc-1")
    deleted = repository.delete_by_id("doc-1")

    assert found["id"] == "doc-1"
    assert deleted is True
    assert client.calls[0]["filters"] == [("id", "doc-1")]
    assert client.calls[1]["filters"] == [("id", "doc-1")]


import asyncio
import sys
from io import BytesIO
from types import ModuleType, SimpleNamespace

from starlette.datastructures import Headers, UploadFile
from app.routers import knowledge as knowledge_router


def test_s3_upload_registers_stable_metadata_and_cleans_temporary_file(monkeypatch, tmp_path):
    events = []
    rag = ModuleType("app.services.knowledge_rag")

    def process(path):
        assert __import__("os").path.exists(path)
        events.append(("index", path))
        return {"pages": 1, "chunks": 3}

    def delete_document(*_args, **_kwargs):
        return 0

    rag.process_and_store_document = process
    rag.delete_document = delete_document
    monkeypatch.setitem(sys.modules, "app.services.knowledge_rag", rag)
    monkeypatch.setattr(knowledge_router, "UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(knowledge_router, "get_supabase_client", lambda: object())

    class FakeRepository:
        def __init__(self, _client):
            pass

        def create_document(self, values):
            events.append(("register", values.copy()))
            return {
                "id": "doc-1",
                **values,
                "created_at": "2026-10-24T16:00:00+00:00",
                "updated_at": "2026-10-24T16:00:00+00:00",
            }

    monkeypatch.setattr(knowledge_router, "KnowledgeDocumentRepository", FakeRepository)

    from app.services import object_storage

    def upload_knowledge_document(filename, file_bytes, content_type, *, prefix):
        events.append(("store", filename, prefix))
        return {
            "storage_provider": "s3",
            "file_key": "knowledge/knowledge_uuid_policy.pdf",
            # Even if an adapter accidentally returns a temporary URL, it must not
            # be persisted or returned as a permanent document URL.
            "file_url": "https://example.invalid/temporary-signed-url",
        }

    monkeypatch.setattr(object_storage, "upload_knowledge_document", upload_knowledge_document)
    file = UploadFile(
        file=BytesIO(b"%PDF-1.7 test"),
        filename="policy.pdf",
        headers=Headers({"content-type": "application/pdf"}),
    )

    result = asyncio.run(
        knowledge_router.upload_document(file, SimpleNamespace(id="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"))
    )

    assert result["success"] is True
    assert result["id"] == "doc-1"
    assert result["file_url"] is None
    assert result["file_key"] == "knowledge/knowledge_uuid_policy.pdf"
    assert [event[0] for event in events] == ["store", "index", "register"]
    registry_values = events[-1][1]
    assert registry_values["storage_provider"] == "s3"
    assert registry_values["file_url"] is None
    assert registry_values["pages"] == 1
    assert registry_values["chunks"] == 3
    assert not __import__("os").path.exists(registry_values["index_source"])
