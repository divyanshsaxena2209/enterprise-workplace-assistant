from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.repositories.management_access_request_repository import ManagementAccessRequestRepository
from app.schemas.auth import CognitoSignupProfile


class FakeTableState:
    def __init__(self):
        self.records = []


class FakeQuery:
    def __init__(self, state):
        self.state = state
        self.action = "select"
        self.fields = "*"
        self.filters = {}
        self.payload = None
        self.ordering = None

    def select(self, fields):
        self.action = "select"
        self.fields = fields
        return self

    def eq(self, key, value):
        self.filters[key] = value
        return self

    def limit(self, _count):
        return self

    def order(self, column, desc=False):
        self.ordering = (column, desc)
        return self

    def insert(self, payload):
        self.action = "insert"
        self.payload = dict(payload)
        return self

    def update(self, payload):
        self.action = "update"
        self.payload = dict(payload)
        return self

    def execute(self):
        matched = [
            row for row in self.state.records
            if all(row.get(key) == value for key, value in self.filters.items())
        ]
        if self.action == "select":
            if self.ordering:
                column, desc = self.ordering
                matched.sort(key=lambda row: row.get(column) or "", reverse=desc)
            return SimpleNamespace(data=[
                {key: value for key, value in row.items() if self.fields == "*" or key in self.fields.split(",")}
                for row in matched[:1] if self.filters.get("profile_id") is not None
            ] if self.filters.get("profile_id") is not None else [
                {key: value for key, value in row.items() if self.fields == "*" or key in self.fields.split(",")}
                for row in matched
            ])
        if self.action == "insert":
            if any(row.get("profile_id") == self.payload.get("profile_id") for row in self.state.records):
                raise RuntimeError("duplicate profile_id")
            self.state.records.append(dict(self.payload))
            return SimpleNamespace(data=[dict(self.payload)])
        if self.action == "update":
            updated = []
            for row in matched:
                row.update(self.payload)
                updated.append(dict(row))
            return SimpleNamespace(data=updated)
        raise AssertionError(f"Unexpected action: {self.action}")


class FakeClient:
    def __init__(self):
        self.request_table = FakeTableState()
        self.rpc_calls = []

    def table(self, _table):
        return FakeQuery(self.request_table)

    def rpc(self, name, args):
        self.rpc_calls.append((name, dict(args)))
        return SimpleNamespace(execute=lambda: SimpleNamespace(data=args["p_decision"] + "D"))


def test_cognito_signup_accepts_management_as_a_request_not_a_role():
    profile = CognitoSignupProfile(
        full_name="Jamie Employee",
        department="Engineering",
        job_title="Engineer",
        requested_access_level="MANAGEMENT",
    )
    assert profile.requested_access_level == "MANAGEMENT"
    assert not hasattr(profile, "role")


def test_cognito_signup_rejects_client_supplied_role_field():
    with pytest.raises(ValidationError):
        CognitoSignupProfile(
            full_name="Jamie Employee",
            department="Engineering",
            job_title="Engineer",
            role="MANAGEMENT",
        )


def test_management_request_submit_is_idempotent_for_pending_request():
    client = FakeClient()
    repo = ManagementAccessRequestRepository(client)

    first = repo.submit("profile-1")
    second = repo.submit("profile-1", request_note="retry")

    assert first["status"] == "PENDING"
    assert second["status"] == "PENDING"
    assert len(client.request_table.records) == 1
    assert client.request_table.records[0]["request_note"] is None


def test_rejected_request_can_be_resubmitted_without_granting_access():
    client = FakeClient()
    client.request_table.records.append({
        "profile_id": "profile-2",
        "requested_role": "MANAGEMENT",
        "status": "REJECTED",
        "reviewer_id": "manager-1",
        "reviewer_note": "Please provide more information.",
        "requested_at": "2026-01-01T00:00:00+00:00",
    })
    repo = ManagementAccessRequestRepository(client)

    result = repo.submit("profile-2", request_note="I now lead the team.")

    assert result["status"] == "PENDING"
    assert result["reviewer_id"] is None
    assert result["reviewer_note"] is None
    assert result["request_note"] == "I now lead the team."
    assert len(client.request_table.records) == 1


def test_review_uses_server_supplied_reviewer_and_decision():
    client = FakeClient()
    repo = ManagementAccessRequestRepository(client)

    status = repo.review(
        profile_id="profile-3",
        decision="APPROVE",
        reviewer_id="manager-1",
        reviewer_note="Verified by a manager.",
    )

    assert status == "APPROVED"
    assert client.rpc_calls == [(
        "review_management_access_request",
        {
            "p_profile_id": "profile-3",
            "p_decision": "APPROVE",
            "p_reviewer_id": "manager-1",
            "p_reviewer_note": "Verified by a manager.",
        },
    )]


def test_review_rejects_unknown_decision_before_rpc():
    client = FakeClient()
    repo = ManagementAccessRequestRepository(client)

    with pytest.raises(Exception, match="Decision must be APPROVE or REJECT"):
        repo.review(
            profile_id="profile-4",
            decision="PROMOTE",
            reviewer_id="employee-1",
        )

    assert client.rpc_calls == []



def test_allowlisted_approval_does_not_report_a_pending_row_as_approved(monkeypatch):
    from app.repositories.management_access_request_repository import ManagementAccessRequestRepository

    class FakeClientWithState:
        def __init__(self, state):
            self.state = state
        def table(self, _name):
            return FakeQuery(self.state)
        def rpc(self, _name, _args):
            raise AssertionError("RPC is not used for the allowlist audit write.")

    state = FakeTableState()
    state.records.append({
        "profile_id": "profile-pending",
        "requested_role": "MANAGEMENT",
        "status": "PENDING",
        "request_note": None,
        "reviewer_note": None,
        "requested_at": "2026-10-01T00:00:00+00:00",
        "reviewed_at": None,
        "updated_at": "2026-10-01T00:00:00+00:00",
    })
    repo = ManagementAccessRequestRepository(FakeClientWithState(state))

    result = repo.mark_allowlisted_approved("profile-pending")

    assert result["status"] == "APPROVED"
    assert state.records[0]["status"] == "APPROVED"
