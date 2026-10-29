from types import SimpleNamespace

from app.services import object_storage, storage_migration


class FakeResponse:
    def __init__(self, data):
        self.data = data


class FakeQuery:
    def __init__(self, client, table):
        self.client = client
        self.table_name = table
        self.operation = "select"
        self.columns = "*"
        self.values = None
        self.filters = []

    def select(self, columns):
        self.columns = columns
        return self

    def update(self, values):
        self.operation = "update"
        self.values = values
        return self

    def order(self, _column):
        return self

    def eq(self, column, value):
        self.filters.append((column, value))
        return self

    def execute(self):
        rows = self.client.rows[self.table_name]
        matching = [
            row for row in rows
            if all(row.get(column) == value for column, value in self.filters)
        ]
        if self.operation == "update":
            for row in matching:
                row.update(self.values)
            return FakeResponse([{"id": row.get("id")} for row in matching])

        columns = [column.strip() for column in self.columns.split(",")]
        if columns == ["*"]:
            return FakeResponse([dict(row) for row in matching])
        return FakeResponse([
            {column: row.get(column) for column in columns}
            for row in matching
        ])


class FakeSupabase:
    def __init__(self):
        self.rows = {
            "knowledge_documents": [{
                "id": "doc-1",
                "filename": "synthetic-policy.pdf",
                "storage_provider": "supabase",
                "file_key": "knowledge_policy_test.pdf",
                "file_url": None,
                "created_at": "2026-01-01T00:00:00Z",
            }],
            "resumes": [
                {
                    "id": f"resume-{n}",
                    "file_name": f"synthetic-{n}.pdf",
                    "file_url": f"supabase://resumes_test_{n}.pdf",
                    "uploaded_at": f"2026-01-0{n}T00:00:00Z",
                }
                for n in range(1, 4)
            ],
        }

    def table(self, table):
        return FakeQuery(self, table)


class FakeS3:
    def __init__(self):
        self.objects = {}
        self.put_calls = []

    def put_object(self, **kwargs):
        self.put_calls.append(kwargs)
        self.objects[kwargs["Key"]] = kwargs["Body"]


def test_source_key_validation_is_prefix_scoped():
    assert storage_migration._validated_source_key(
        "knowledge_policy.pdf", prefix="knowledge"
    ) == "knowledge_policy.pdf"
    assert storage_migration._validated_source_key(
        "supabase://resumes_candidate.pdf", prefix="resumes"
    ) == "resumes_candidate.pdf"
    assert storage_migration._validated_source_key(
        "supabase://knowledge_private.pdf", prefix="resumes"
    ) is None
    assert storage_migration._validated_source_key(
        "../resumes_candidate.pdf", prefix="resumes"
    ) is None


def test_dry_run_reports_referenced_objects_without_writing(monkeypatch):
    client = FakeSupabase()
    monkeypatch.setattr(storage_migration, "get_supabase_client", lambda: client)
    monkeypatch.setattr(storage_migration.settings, "ENVIRONMENT", "staging")
    monkeypatch.setattr(storage_migration.settings, "STORAGE_PROVIDER", "s3")
    monkeypatch.setattr(storage_migration.settings, "AWS_S3_BUCKET", "ewa-private-documents-staging")

    def should_not_download(*_args, **_kwargs):
        raise AssertionError("Dry run must not copy object bytes")

    monkeypatch.setattr(object_storage, "download_supabase_object_bytes", should_not_download)

    result = storage_migration.migrate_supabase_objects_to_s3(dry_run=True)

    assert result["dry_run"] is True
    assert result["knowledge_documents"]["eligible"] == 1
    assert result["resumes"]["eligible"] == 3
    assert result["knowledge_documents"]["migrated"] == 0
    assert client.rows["knowledge_documents"][0]["storage_provider"] == "supabase"
    assert client.rows["resumes"][0]["file_url"].startswith("supabase://")


def test_migration_verifies_copies_and_updates_only_references(monkeypatch):
    client = FakeSupabase()
    fake_s3 = FakeS3()
    monkeypatch.setattr(storage_migration, "get_supabase_client", lambda: client)
    monkeypatch.setattr(storage_migration.settings, "ENVIRONMENT", "staging")
    monkeypatch.setattr(storage_migration.settings, "STORAGE_PROVIDER", "s3")
    monkeypatch.setattr(storage_migration.settings, "AWS_S3_BUCKET", "ewa-private-documents-staging")
    monkeypatch.setattr(storage_migration.settings, "AWS_REGION", "ap-south-1")
    monkeypatch.setattr(
        object_storage,
        "download_supabase_object_bytes",
        lambda key, *, prefix: f"source:{prefix}:{key}".encode(),
    )
    monkeypatch.setattr(
        object_storage,
        "download_s3_object_bytes",
        lambda key, *, prefix: fake_s3.objects[key],
    )
    monkeypatch.setitem(
        __import__("sys").modules,
        "boto3",
        SimpleNamespace(client=lambda service, region_name: fake_s3),
    )

    result = storage_migration.migrate_supabase_objects_to_s3(dry_run=False)

    assert result["success"] is True
    assert result["knowledge_documents"]["migrated"] == 1
    assert result["resumes"]["migrated"] == 3
    knowledge = client.rows["knowledge_documents"][0]
    assert knowledge["storage_provider"] == "s3"
    assert knowledge["file_key"] == "knowledge/knowledge_policy_test.pdf"
    assert knowledge["file_url"] is None
    assert all(
        row["file_url"].startswith("s3://resumes/resumes_test_")
        for row in client.rows["resumes"]
    )
    assert len(fake_s3.put_calls) == 4
    # Original Supabase objects aren't deleted or modified by this migration.
    assert result["source_objects_retained"] is True


def test_migration_refuses_non_staging(monkeypatch):
    monkeypatch.setattr(storage_migration.settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(storage_migration.settings, "STORAGE_PROVIDER", "s3")
    monkeypatch.setattr(storage_migration.settings, "AWS_S3_BUCKET", "ewa-private-documents-staging")

    try:
        storage_migration.migrate_supabase_objects_to_s3(dry_run=True)
    except RuntimeError as exc:
        assert "only in staging" in str(exc)
    else:
        raise AssertionError("Non-staging migration must be rejected")
