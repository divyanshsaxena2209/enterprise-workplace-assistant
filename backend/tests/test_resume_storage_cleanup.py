"""Regression tests for resume object cleanup around database persistence."""
import importlib
import sys
from io import BytesIO
from types import ModuleType, SimpleNamespace

import pytest
from starlette.datastructures import Headers, UploadFile

from app.core.exceptions import DatabaseError
from app.services import object_storage


class FakeParsedResume:
    full_name = "Test Candidate"
    email = "candidate@example.invalid"
    phone = None

    def model_dump(self):
        return {"full_name": self.full_name, "email": self.email, "phone": self.phone}


class FakeResumeParser:
    def extract_text(self, _file_bytes, _filename):
        return "Test resume text"

    def parse_with_ai(self, _text):
        return FakeParsedResume()


def load_resume_router(monkeypatch):
    # Stub the parser module before importing the route. This keeps this focused
    # routing test independent of optional Gemini/PDF runtime packages.
    parser_module = ModuleType("app.services.resume_parser")
    parser_module.ResumeParserService = FakeResumeParser
    monkeypatch.setitem(sys.modules, "app.services.resume_parser", parser_module)
    sys.modules.pop("app.routers.resume", None)
    return importlib.import_module("app.routers.resume")


def make_upload():
    return UploadFile(
        file=BytesIO(b"%PDF-1.7 test bytes"),
        filename="resume.pdf",
        headers=Headers({"content-type": "application/pdf"}),
    )


def test_resume_database_failure_attempts_prefix_scoped_object_cleanup(monkeypatch):
    router = load_resume_router(monkeypatch)
    monkeypatch.setattr(router, "get_supabase_client", lambda: object())
    monkeypatch.setattr(
        object_storage,
        "upload_knowledge_document",
        lambda *_args, **_kwargs: {
            "storage_provider": "s3",
            "file_key": "resumes/resumes_uuid_resume.pdf",
            "file_url": None,
        },
    )
    cleanup_calls = []
    monkeypatch.setattr(
        object_storage,
        "delete_resume_object",
        lambda provider, key, url=None: cleanup_calls.append((provider, key, url)),
    )

    class FailingRepository:
        def __init__(self, _client):
            pass

        def create_candidate_with_resume(self, **_kwargs):
            raise RuntimeError("database unavailable")

    monkeypatch.setattr(router, "CandidateRepository", FailingRepository)

    with pytest.raises(DatabaseError, match="object cleanup was attempted"):
        router.upload_resume(make_upload(), SimpleNamespace(id="employee-1"))

    assert cleanup_calls == [("s3", "resumes/resumes_uuid_resume.pdf", None)]


def test_resume_persists_s3_locator_not_expiring_url(monkeypatch):
    router = load_resume_router(monkeypatch)
    monkeypatch.setattr(router, "get_supabase_client", lambda: object())
    monkeypatch.setattr(
        object_storage,
        "upload_knowledge_document",
        lambda *_args, **_kwargs: {
            "storage_provider": "s3",
            "file_key": "resumes/resumes_uuid_resume.pdf",
            "file_url": None,
        },
    )
    monkeypatch.setattr(
        object_storage,
        "delete_resume_object",
        lambda *_args, **_kwargs: pytest.fail("successful persistence must not delete the resume"),
    )

    class SuccessfulRepository:
        def __init__(self, _client):
            pass

        def create_candidate_with_resume(self, *, candidate_data, resume_data):
            assert candidate_data["full_name"] == "Test Candidate"
            assert resume_data["file_url"] == "s3://resumes/resumes_uuid_resume.pdf"
            return "candidate-1", "resume-1"

    monkeypatch.setattr(router, "CandidateRepository", SuccessfulRepository)

    result = router.upload_resume(make_upload(), SimpleNamespace(id="employee-1"))

    assert result.candidate_id == "candidate-1"
    assert result.resume_id == "resume-1"


def test_supabase_resume_persists_stable_provider_key(monkeypatch):
    router = load_resume_router(monkeypatch)
    monkeypatch.setattr(router, "get_supabase_client", lambda: object())
    monkeypatch.setattr(
        object_storage,
        "upload_knowledge_document",
        lambda *_args, **_kwargs: {
            "storage_provider": "supabase",
            "file_key": "resumes_uuid_resume.pdf",
            "file_url": None,
        },
    )
    monkeypatch.setattr(
        object_storage,
        "delete_resume_object",
        lambda *_args, **_kwargs: pytest.fail("successful persistence must not delete the resume"),
    )

    class SuccessfulRepository:
        def __init__(self, _client):
            pass

        def create_candidate_with_resume(self, *, candidate_data, resume_data):
            assert resume_data["file_url"] == "supabase://resumes_uuid_resume.pdf"
            return "candidate-2", "resume-2"

    monkeypatch.setattr(router, "CandidateRepository", SuccessfulRepository)
    result = router.upload_resume(make_upload(), SimpleNamespace(id="employee-2"))
    assert result.candidate_id == "candidate-2"
    assert result.resume_id == "resume-2"
