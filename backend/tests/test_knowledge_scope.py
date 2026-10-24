"""Regression tests for department-scoped knowledge listing and Qdrant retrieval."""
import importlib
import sys
from types import ModuleType, SimpleNamespace

import pytest
from fastapi import HTTPException
from qdrant_client.http import models

from app.core.enums import UserRole
from app.services.knowledge_scope import (
    build_department_scope_filter,
    document_scope_visible,
    normalize_department_scope,
    normalize_department_scope_key,
)


def test_scope_normalization_and_employee_visibility_are_case_insensitive():
    assert normalize_department_scope("  all  ") == "ALL"
    assert normalize_department_scope(" Engineering ") == "Engineering"
    assert normalize_department_scope_key(" Engineering ") == "engineering"
    assert document_scope_visible("ALL", "Engineering")
    assert document_scope_visible("engineering", "Engineering")
    assert not document_scope_visible("HR", "Engineering")
    assert not document_scope_visible("HR", None)
    assert document_scope_visible("HR", None, is_management=True)


def test_qdrant_filter_includes_global_matching_department_and_legacy_documents():
    filter_value = build_department_scope_filter("Engineering")

    assert isinstance(filter_value, models.Filter)
    assert filter_value.should is not None
    assert len(filter_value.should) == 3
    assert filter_value.should[0].field.key == "metadata.department_scope_key"
    assert filter_value.should[0].field.match.value == "all"
    assert filter_value.should[1].field.match.value == "engineering"
    assert filter_value.should[2].is_null.key == "metadata.department_scope_key"


def test_management_query_has_no_department_filter():
    assert build_department_scope_filter(None) is None


def load_knowledge_router(monkeypatch):
    rag_module = ModuleType("app.services.knowledge_rag")
    rag_module.retrieve_and_answer = lambda *_args, **_kwargs: {"answer": "ok", "sources": []}
    rag_module.process_and_store_document = lambda *_args, **_kwargs: {"pages": 0, "chunks": 0}
    rag_module.delete_document = lambda *_args, **_kwargs: 0
    monkeypatch.setitem(sys.modules, "app.services.knowledge_rag", rag_module)
    sys.modules.pop("app.routers.knowledge", None)
    return importlib.import_module("app.routers.knowledge")


def test_employee_document_list_filters_other_departments(monkeypatch):
    router = load_knowledge_router(monkeypatch)
    records = [
        {"id": "global", "filename": "company-policy.pdf", "department_scope": "ALL"},
        {"id": "engineering", "filename": "engineering.pdf", "department_scope": "Engineering"},
        {"id": "hr", "filename": "hr.pdf", "department_scope": "HR"},
        {"id": "legacy", "filename": "legacy.pdf"},
    ]

    class FakeRepository:
        def list_documents(self):
            return records

    monkeypatch.setattr(router, "_document_repository", lambda: FakeRepository())
    employee = SimpleNamespace(
        id="employee-1",
        role=UserRole.EMPLOYEE,
        department="engineering",
    )

    result = router.list_knowledge_documents(employee)

    assert [row["id"] for row in result] == ["global", "engineering", "legacy"]


def test_employee_cannot_get_signed_url_for_another_departments_document(monkeypatch):
    router = load_knowledge_router(monkeypatch)
    record = {
        "id": "hr-doc",
        "filename": "hr-policy.pdf",
        "storage_provider": "s3",
        "file_key": "knowledge/hr-policy.pdf",
        "department_scope": "HR",
    }

    class FakeRepository:
        def get_by_file_key(self, _key):
            return record

    monkeypatch.setattr(router, "_document_repository", lambda: FakeRepository())
    monkeypatch.setattr(
        "app.services.object_storage.create_knowledge_document_download_url",
        lambda *_args, **_kwargs: pytest.fail("cross-department URL must not be minted"),
    )
    employee = SimpleNamespace(
        id="employee-1",
        role=UserRole.EMPLOYEE,
        department="engineering",
    )

    with pytest.raises(HTTPException) as error:
        router.get_document_download_url("knowledge/hr-policy.pdf", employee)

    assert error.value.status_code == 404


def test_employee_can_get_signed_url_for_company_wide_document(monkeypatch):
    router = load_knowledge_router(monkeypatch)
    record = {
        "id": "global-doc",
        "filename": "company-policy.pdf",
        "storage_provider": "s3",
        "file_key": "knowledge/company-policy.pdf",
        "department_scope": "ALL",
    }

    class FakeRepository:
        def get_by_file_key(self, _key):
            return record

    monkeypatch.setattr(router, "_document_repository", lambda: FakeRepository())
    monkeypatch.setattr(
        "app.services.object_storage.create_knowledge_document_download_url",
        lambda key: f"https://signed.invalid/{key}",
    )
    employee = SimpleNamespace(
        id="employee-1",
        role=UserRole.EMPLOYEE,
        department="engineering",
    )

    assert router.get_document_download_url("knowledge/company-policy.pdf", employee) == {
        "file_url": "https://signed.invalid/knowledge/company-policy.pdf"
    }
