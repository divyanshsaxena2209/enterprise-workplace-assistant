"""Department-aware access and retrieval scope for company knowledge documents."""
from __future__ import annotations


def normalize_department_scope(value: str | None) -> str:
    """Return a stable display value; empty or ALL means company-wide."""
    cleaned = (value or "").strip()
    return "ALL" if not cleaned or cleaned.casefold() == "all" else cleaned


def normalize_department_scope_key(value: str | None) -> str:
    """Normalized value stored in Qdrant payloads for case-insensitive matching."""
    cleaned = normalize_department_scope(value)
    return "all" if cleaned == "ALL" else cleaned.casefold()


def document_scope_visible(
    document_scope: str | None,
    user_department: str | None,
    *,
    is_management: bool = False,
) -> bool:
    """Management can see all scopes; employees can see global and own-department docs."""
    if is_management:
        return True
    scope_key = normalize_department_scope_key(document_scope)
    department_key = normalize_department_scope_key(user_department)
    if scope_key == "review_required":
        return False
    return scope_key == "all" or (department_key != "all" and scope_key == department_key)


def build_department_scope_filter(department_scope: str | None):
    """Build a Qdrant filter; None means the caller has management-wide access.

    Points without an explicit scope are excluded (fail closed). Reindex legacy
    documents with a manager-selected scope before making them searchable again.
    """
    if department_scope is None:
        return None

    from qdrant_client.http import models

    field_key = "metadata.department_scope_key"
    # Missing metadata is not public by default: only explicit company-wide
    # and matching-department scopes are visible to employee queries.
    should = [
        models.FieldCondition(
            key=field_key,
            match=models.MatchValue(value="all"),
        ),
    ]
    department_key = normalize_department_scope_key(department_scope)
    if department_key and department_key != "all":
        should.insert(
            1,
            models.FieldCondition(
                key=field_key,
                match=models.MatchValue(value=department_key),
            ),
        )
    return models.Filter(should=should)
