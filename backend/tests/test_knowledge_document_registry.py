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
