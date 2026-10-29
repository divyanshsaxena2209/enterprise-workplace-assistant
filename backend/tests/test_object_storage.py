from types import SimpleNamespace

import pytest

from app.services import object_storage


class FakeS3:
    def __init__(self):
        self.put_calls = []
        self.delete_calls = []
        self.presign_calls = []

    def put_object(self, **kwargs):
        self.put_calls.append(kwargs)

    def delete_object(self, **kwargs):
        self.delete_calls.append(kwargs)

    def generate_presigned_url(self, operation, *, Params, ExpiresIn):
        self.presign_calls.append((operation, Params, ExpiresIn))
        return "https://example.invalid/presigned"


def install_fake_boto3(monkeypatch, fake_s3):
    monkeypatch.setitem(
        __import__("sys").modules,
        "boto3",
        SimpleNamespace(client=lambda service, region_name: fake_s3),
    )


def test_s3_upload_uses_private_prefix_and_server_side_encryption(monkeypatch):
    fake_s3 = FakeS3()
    install_fake_boto3(monkeypatch, fake_s3)
    monkeypatch.setattr(object_storage.settings, "STORAGE_PROVIDER", "s3")
    monkeypatch.setattr(object_storage.settings, "AWS_REGION", "ap-south-1")
    monkeypatch.setattr(object_storage.settings, "AWS_S3_BUCKET", "ewa-private-documents")
    monkeypatch.setattr(object_storage.settings, "S3_PRESIGNED_URL_TTL_SECONDS", 900)

    result = object_storage.upload_knowledge_document(
        "resume one.pdf", b"pdf-bytes", "application/pdf", prefix="resumes"
    )

    assert result["storage_provider"] == "s3"
    assert result["file_key"].startswith("resumes/resumes_")
    assert result["file_url"] is None
    assert fake_s3.presign_calls == []
    assert fake_s3.put_calls[0]["Bucket"] == "ewa-private-documents"
    assert fake_s3.put_calls[0]["Body"] == b"pdf-bytes"
    assert fake_s3.put_calls[0]["ServerSideEncryption"] == "AES256"
    assert fake_s3.put_calls[0]["Key"].startswith("resumes/")


@pytest.mark.parametrize(
    "key",
    [
        "../secret.txt",
        "other/private.txt",
        "",
        "knowledge/../secret.txt",
        "resumes/private.pdf",
        "knowledge\\\\private.pdf",
    ],
)
def test_knowledge_delete_rejects_keys_outside_knowledge_prefix(monkeypatch, key):
    fake_s3 = FakeS3()
    install_fake_boto3(monkeypatch, fake_s3)
    monkeypatch.setattr(object_storage.settings, "AWS_REGION", "ap-south-1")
    monkeypatch.setattr(object_storage.settings, "AWS_S3_BUCKET", "ewa-private-documents")

    with pytest.raises(ValueError):
        object_storage.delete_knowledge_document_object("s3", key, None)

    assert fake_s3.delete_calls == []


def test_knowledge_delete_accepts_only_knowledge_objects(monkeypatch):
    fake_s3 = FakeS3()
    install_fake_boto3(monkeypatch, fake_s3)
    monkeypatch.setattr(object_storage.settings, "AWS_REGION", "ap-south-1")
    monkeypatch.setattr(object_storage.settings, "AWS_S3_BUCKET", "ewa-private-documents")

    object_storage.delete_knowledge_document_object("s3", "knowledge/doc-1.pdf", None)

    assert [call["Key"] for call in fake_s3.delete_calls] == ["knowledge/doc-1.pdf"]


def test_supabase_knowledge_delete_refuses_resume_object_keys(monkeypatch):
    class FakeStorageBucket:
        def __init__(self):
            self.remove_calls = []

        def remove(self, keys):
            self.remove_calls.append(keys)

    bucket = FakeStorageBucket()
    fake_client = SimpleNamespace(storage=SimpleNamespace(from_=lambda _name: bucket))
    monkeypatch.setattr("app.db.supabase.get_supabase_client", lambda: fake_client)

    with pytest.raises(ValueError):
        object_storage.delete_knowledge_document_object(
            "supabase", "resumes_123456_resume.pdf", None
        )

    assert bucket.remove_calls == []


def test_supabase_knowledge_delete_removes_legacy_knowledge_key(monkeypatch):
    class FakeStorageBucket:
        def __init__(self):
            self.remove_calls = []

        def remove(self, keys):
            self.remove_calls.append(keys)

    bucket = FakeStorageBucket()
    fake_client = SimpleNamespace(storage=SimpleNamespace(from_=lambda _name: bucket))
    monkeypatch.setattr("app.db.supabase.get_supabase_client", lambda: fake_client)

    object_storage.delete_knowledge_document_object(
        "supabase", "knowledge_123456_policy.pdf", None
    )

    assert bucket.remove_calls == [["knowledge_123456_policy.pdf"]]


def test_knowledge_download_url_does_not_allow_resume_keys(monkeypatch):
    fake_s3 = FakeS3()
    install_fake_boto3(monkeypatch, fake_s3)
    monkeypatch.setattr(object_storage.settings, "AWS_REGION", "ap-south-1")
    monkeypatch.setattr(object_storage.settings, "AWS_S3_BUCKET", "ewa-private-documents")

    with pytest.raises(ValueError):
        object_storage.create_knowledge_document_download_url("resumes/private.pdf")

    assert fake_s3.presign_calls == []


def test_resume_download_url_is_expiring_and_prefix_scoped(monkeypatch):
    fake_s3 = FakeS3()
    install_fake_boto3(monkeypatch, fake_s3)
    monkeypatch.setattr(object_storage.settings, "AWS_REGION", "ap-south-1")
    monkeypatch.setattr(object_storage.settings, "AWS_S3_BUCKET", "ewa-private-documents")
    monkeypatch.setattr(object_storage.settings, "S3_PRESIGNED_URL_TTL_SECONDS", 900)

    url = object_storage.create_resume_download_url("resumes/resume-1.pdf")

    assert url == "https://example.invalid/presigned"
    assert fake_s3.presign_calls[0][1]["Key"] == "resumes/resume-1.pdf"
    assert fake_s3.presign_calls[0][2] == 900


def test_resume_delete_accepts_only_resume_prefix_for_s3(monkeypatch):
    fake_s3 = FakeS3()
    install_fake_boto3(monkeypatch, fake_s3)
    monkeypatch.setattr(object_storage.settings, "AWS_REGION", "ap-south-1")
    monkeypatch.setattr(object_storage.settings, "AWS_S3_BUCKET", "ewa-private-documents")

    object_storage.delete_resume_object("s3", "resumes/resume-1.pdf")

    assert [call["Key"] for call in fake_s3.delete_calls] == ["resumes/resume-1.pdf"]


@pytest.mark.parametrize("key", ["knowledge/policy.pdf", "../resume.pdf", "resumes/../policy.pdf", "resumes\\\\resume.pdf", ""])
def test_resume_delete_rejects_keys_outside_resume_prefix(monkeypatch, key):
    fake_s3 = FakeS3()
    install_fake_boto3(monkeypatch, fake_s3)
    monkeypatch.setattr(object_storage.settings, "AWS_REGION", "ap-south-1")
    monkeypatch.setattr(object_storage.settings, "AWS_S3_BUCKET", "ewa-private-documents")

    with pytest.raises(ValueError):
        object_storage.delete_resume_object("s3", key)

    assert fake_s3.delete_calls == []


def test_resume_delete_removes_only_resumes_bucket_object_in_supabase(monkeypatch):
    class FakeStorageBucket:
        def __init__(self):
            self.remove_calls = []

        def remove(self, keys):
            self.remove_calls.append(keys)

    bucket = FakeStorageBucket()
    fake_client = SimpleNamespace(storage=SimpleNamespace(from_=lambda _name: bucket))
    monkeypatch.setattr("app.db.supabase.get_supabase_client", lambda: fake_client)

    object_storage.delete_resume_object("supabase", "resumes_uuid_resume.pdf")

    assert bucket.remove_calls == [["resumes_uuid_resume.pdf"]]


def test_supabase_upload_persists_key_without_public_url_and_signs_only_on_demand(monkeypatch):
    from app.db import supabase as supabase_module

    class FakeStorageBucket:
        def __init__(self):
            self.upload_calls = []
            self.signed_calls = []
            self.public_url_calls = 0

        def upload(self, **kwargs):
            self.upload_calls.append(kwargs)

        def get_public_url(self, _path):
            self.public_url_calls += 1
            raise AssertionError("New document uploads must not request a public URL")

        def create_signed_url(self, path, ttl):
            self.signed_calls.append((path, ttl))
            return {"signedURL": "https://staging.supabase.co/storage/v1/object/sign/resumes/file?token=test"}

    bucket = FakeStorageBucket()
    client = SimpleNamespace(storage=SimpleNamespace(from_=lambda _name: bucket))
    monkeypatch.setattr(supabase_module, "get_supabase_client", lambda: client)
    monkeypatch.setattr(object_storage.settings, "STORAGE_PROVIDER", "supabase")
    monkeypatch.setattr(object_storage.settings, "S3_PRESIGNED_URL_TTL_SECONDS", 900)

    stored = object_storage.upload_knowledge_document(
        "policy.pdf", b"%PDF-bytes", "application/pdf", prefix="knowledge"
    )
    assert stored["storage_provider"] == "supabase"
    assert stored["file_key"].startswith("knowledge_")
    assert stored["file_url"] is None
    assert bucket.public_url_calls == 0
    assert bucket.upload_calls[0]["path"] == stored["file_key"]

    url = object_storage.create_knowledge_document_download_url(
        stored["file_key"], storage_provider="supabase"
    )
    assert url == "https://staging.supabase.co/storage/v1/object/sign/resumes/file?token=test"
    assert bucket.signed_calls == [(stored["file_key"], 900)]


@pytest.mark.parametrize("key", ["resumes/other.pdf", "../knowledge_policy.pdf", "knowledge\\\\policy.pdf", ""])
def test_supabase_knowledge_signed_url_rejects_out_of_scope_keys(monkeypatch, key):
    with pytest.raises(ValueError):
        object_storage.create_knowledge_document_download_url(key, storage_provider="supabase")


def test_supabase_resume_signed_url_requires_resume_prefix(monkeypatch):
    from app.db import supabase as supabase_module

    class FakeBucket:
        def __init__(self):
            self.signed = []

        def create_signed_url(self, path, ttl):
            self.signed.append((path, ttl))
            return {"signedURL": "https://signed.invalid/resume"}

    bucket = FakeBucket()
    client = SimpleNamespace(storage=SimpleNamespace(from_=lambda _name: bucket))
    monkeypatch.setattr(supabase_module, "get_supabase_client", lambda: client)
    monkeypatch.setattr(object_storage.settings, "S3_PRESIGNED_URL_TTL_SECONDS", 900)

    assert object_storage.create_resume_download_url(
        "resumes_abc_resume.pdf", storage_provider="supabase"
    ) == "https://signed.invalid/resume"
    assert bucket.signed == [("resumes_abc_resume.pdf", 900)]
    with pytest.raises(ValueError):
        object_storage.create_resume_download_url("knowledge_policy.pdf", storage_provider="supabase")


def test_extract_legacy_supabase_resume_urls_without_fetching_them():
    url = (
        "https://project.supabase.co/storage/v1/object/public/resumes/"
        "resumes_uuid_resume%20one.pdf"
    )
    assert object_storage.extract_supabase_object_key_from_url(
        url, prefix="resumes"
    ) == "resumes_uuid_resume one.pdf"

    assert object_storage.extract_supabase_object_key_from_url(
        "https://example.invalid/storage/v1/object/public/other/file.pdf",
        prefix="resumes",
    ) is None

    with pytest.raises(ValueError):
        object_storage.extract_supabase_object_key_from_url(
            "https://project.supabase.co/storage/v1/object/public/resumes/knowledge_policy.pdf",
            prefix="resumes",
        )


def test_supabase_resume_download_reads_only_validated_resume_object(monkeypatch):
    from app.db import supabase as supabase_module

    class FakeBucket:
        def __init__(self):
            self.downloaded = []

        def download(self, path):
            self.downloaded.append(path)
            return b"private-resume-bytes"

    bucket = FakeBucket()
    client = SimpleNamespace(storage=SimpleNamespace(from_=lambda _name: bucket))
    monkeypatch.setattr(supabase_module, "get_supabase_client", lambda: client)

    assert object_storage.download_supabase_object_bytes(
        "resumes_uuid_resume.pdf", prefix="resumes"
    ) == b"private-resume-bytes"
    assert bucket.downloaded == ["resumes_uuid_resume.pdf"]

    with pytest.raises(ValueError):
        object_storage.download_supabase_object_bytes(
            "knowledge_policy.pdf", prefix="resumes"
        )
    assert bucket.downloaded == ["resumes_uuid_resume.pdf"]


@pytest.mark.parametrize(
    ("stored_url", "expected_provider", "expected_key"),
    [
        (
            "s3://resumes/resumes_uuid_candidate_resume.docx",
            "s3",
            "resumes/resumes_uuid_candidate_resume.docx",
        ),
        (
            "supabase://resumes_uuid_legacy_resume.pdf",
            "supabase",
            "resumes_uuid_legacy_resume.pdf",
        ),
        (
            "https://project.supabase.co/storage/v1/object/sign/resumes/"
            "resumes_uuid_legacy_resume.pdf?token=test",
            "supabase",
            "resumes_uuid_legacy_resume.pdf",
        ),
    ],
)
def test_application_resume_detail_signs_s3_supabase_and_legacy_urls(
    monkeypatch, stored_url, expected_provider, expected_key
):
    from app.repositories.application_repository import ApplicationRepository

    calls = []

    def fake_signed_url(key, *, storage_provider="s3"):
        calls.append((key, storage_provider))
        return f"https://download.invalid/{storage_provider}/resume"

    monkeypatch.setattr(
        object_storage, "create_resume_download_url", fake_signed_url
    )

    parsed = {
        "full_name": None,
        "email": None,
        "phone": None,
        "skills": None,
        "experience": None,
        "education": None,
        "certifications": None,
        "projects": None,
        "previous_companies": None,
    }
    row = {
        "id": "resume-test-id",
        "candidate_id": "candidate-test-id",
        "file_url": stored_url,
        "parsed_json": parsed,
        "uploaded_at": "2026-10-26T16:19:06.771236+00:00",
    }

    result = ApplicationRepository._resume_from_row(row)

    assert result is not None
    assert result.file_url == f"https://download.invalid/{expected_provider}/resume"
    assert calls == [(expected_key, expected_provider)]
