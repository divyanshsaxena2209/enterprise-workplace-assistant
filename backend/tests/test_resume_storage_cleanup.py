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


@pytest.mark.parametrize(
    "stored_locator",
    [
        "supabase://resumes_uuid_resume.pdf",
        "https://staging.supabase.co/storage/v1/object/public/resumes/resumes_uuid_resume.pdf",
    ],
)
def test_candidate_detail_converts_supabase_resume_locator_to_signed_url(monkeypatch, stored_locator):
    from app.repositories.candidate_repository import CandidateRepository

    candidate = {
        "id": "candidate-1",
        "full_name": "Test Candidate",
        "email": "candidate@example.invalid",
        "phone": None,
        "created_at": "2026-10-24T00:00:00+00:00",
        "updated_at": "2026-10-24T00:00:00+00:00",
        "is_deleted": False,
    }
    resume = {
        "id": "resume-1",
        "candidate_id": "candidate-1",
        "file_url": stored_locator,
        "parsed_data": {
            "full_name": "Test Candidate",
            "email": "candidate@example.invalid",
            "phone": None,
            "skills": [],
            "experience": [],
            "education": [],
            "certifications": [],
            "projects": [],
            "previous_companies": [],
        },
        "status": "UPLOADED",
        "created_at": "2026-10-24T00:00:00+00:00",
    }

    class FakeQuery:
        def __init__(self, rows):
            self.rows = rows

        def select(self, *_args, **_kwargs):
            return self

        def eq(self, *_args, **_kwargs):
            return self

        def order(self, *_args, **_kwargs):
            return self

        def limit(self, *_args, **_kwargs):
            return self

        def execute(self):
            return SimpleNamespace(data=self.rows)

    class FakeClient:
        def table(self, table_name):
            return FakeQuery([candidate] if table_name == "candidates" else [resume])

    signed_calls = []
    monkeypatch.setattr(
        object_storage,
        "create_resume_download_url",
        lambda key, storage_provider="s3": (
            signed_calls.append((key, storage_provider)) or "https://signed.invalid/resume?token=short-lived"
        ),
    )

    details = CandidateRepository(FakeClient()).get_candidate_by_id("candidate-1")

    assert details.resume is not None
    assert details.resume.file_url == "https://signed.invalid/resume?token=short-lived"
    assert signed_calls == [("resumes_uuid_resume.pdf", "supabase")]

class _ResumePersistenceQuery:
    def __init__(self, client, table_name):
        self.client = client
        self.table_name = table_name
        self.action = None
        self.payload = None
        self.filters = {}

    def insert(self, payload):
        self.action = "insert"
        self.payload = payload
        self.client.inserted_payloads[self.table_name] = payload
        return self

    def delete(self):
        self.action = "delete"
        return self

    def eq(self, key, value):
        self.filters[key] = value
        return self

    def execute(self):
        if self.action == "delete" and self.table_name == "candidates":
            self.client.deleted_candidate_ids.append(self.filters.get("id"))
            return SimpleNamespace(data=[])
        if self.action == "insert" and self.table_name == "candidates":
            return SimpleNamespace(data=[{"id": "candidate-test-id"}])
        if self.action == "insert" and self.table_name == "resumes":
            if self.client.fail_resume_insert:
                raise RuntimeError("PGRST204")
            return SimpleNamespace(data=[{"id": "resume-test-id"}])
        raise AssertionError(f"Unexpected query: {self.table_name} / {self.action}")


class _ResumePersistenceClient:
    def __init__(self, fail_resume_insert=False):
        self.fail_resume_insert = fail_resume_insert
        self.inserted_payloads = {}
        self.deleted_candidate_ids = []

    def table(self, table_name):
        return _ResumePersistenceQuery(self, table_name)


def test_candidate_resume_insert_matches_live_supabase_schema():
    from app.repositories.candidate_repository import CandidateRepository

    client = _ResumePersistenceClient()
    candidate_id, resume_id = CandidateRepository(client).create_candidate_with_resume(
        candidate_data={"full_name": "Test Candidate", "email": "candidate@example.invalid"},
        resume_data={
            "file_name": "resume.pdf",
            "file_url": "supabase://resumes_test_resume.pdf",
            "parsed_json": {"full_name": "Test Candidate", "skills": ["Python"]},
        },
    )

    assert candidate_id == "candidate-test-id"
    assert resume_id == "resume-test-id"
    assert client.inserted_payloads["resumes"] == {
        "candidate_id": "candidate-test-id",
        "file_name": "resume.pdf",
        "file_url": "supabase://resumes_test_resume.pdf",
        "parsed_json": {"full_name": "Test Candidate", "skills": ["Python"]},
    }


def test_failed_resume_insert_rolls_back_new_candidate():
    from app.repositories.candidate_repository import CandidateRepository

    client = _ResumePersistenceClient(fail_resume_insert=True)
    with pytest.raises(DatabaseError, match="Failed to save candidate and resume data"):
        CandidateRepository(client).create_candidate_with_resume(
            candidate_data={"full_name": "Test Candidate", "email": "candidate@example.invalid"},
            resume_data={
                "file_name": "resume.pdf",
                "file_url": "supabase://resumes_test_resume.pdf",
                "parsed_json": {"full_name": "Test Candidate"},
            },
        )

    assert client.deleted_candidate_ids == ["candidate-test-id"]


def test_resume_response_accepts_current_supabase_resume_columns():
    from app.schemas.resume import ResumeResponse

    response = ResumeResponse.model_validate({
        "id": "resume-test-id",
        "candidate_id": "candidate-test-id",
        "file_name": "resume.pdf",
        "file_url": "supabase://resumes_test_resume.pdf",
        "parsed_json": {
            "full_name": "Test Candidate",
            "email": None,
            "phone": None,
            "skills": ["Python"],
            "experience": [],
            "education": [],
            "certifications": [],
            "projects": [],
            "previous_companies": [],
        },
        "uploaded_at": "2026-10-25T19:33:00Z",
    })

    assert response.parsed_data.full_name == "Test Candidate"
    assert response.status == "UPLOADED"
    assert response.created_at.isoformat().startswith("2026-10-25T19:33:00")

