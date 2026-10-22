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
    assert result["file_url"] == "https://example.invalid/presigned"
    assert fake_s3.put_calls[0]["Bucket"] == "ewa-private-documents"
    assert fake_s3.put_calls[0]["Body"] == b"pdf-bytes"
    assert fake_s3.put_calls[0]["ServerSideEncryption"] == "AES256"
    assert fake_s3.put_calls[0]["Key"].startswith("resumes/")


@pytest.mark.parametrize("key", ["../secret.txt", "other/private.txt", "", "knowledge/../secret.txt"])
def test_delete_s3_object_rejects_keys_outside_allowed_prefixes(monkeypatch, key):
    fake_s3 = FakeS3()
    install_fake_boto3(monkeypatch, fake_s3)
    monkeypatch.setattr(object_storage.settings, "AWS_REGION", "ap-south-1")
    monkeypatch.setattr(object_storage.settings, "AWS_S3_BUCKET", "ewa-private-documents")

    with pytest.raises(ValueError):
        object_storage.delete_knowledge_document_object("s3", key, None)

    assert fake_s3.delete_calls == []


def test_delete_s3_object_accepts_knowledge_and_resume_keys(monkeypatch):
    fake_s3 = FakeS3()
    install_fake_boto3(monkeypatch, fake_s3)
    monkeypatch.setattr(object_storage.settings, "AWS_REGION", "ap-south-1")
    monkeypatch.setattr(object_storage.settings, "AWS_S3_BUCKET", "ewa-private-documents")

    object_storage.delete_knowledge_document_object("s3", "knowledge/doc-1.pdf", None)
    object_storage.delete_knowledge_document_object("s3", "resumes/resume-1.pdf", None)

    assert [call["Key"] for call in fake_s3.delete_calls] == [
        "knowledge/doc-1.pdf",
        "resumes/resume-1.pdf",
    ]


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
