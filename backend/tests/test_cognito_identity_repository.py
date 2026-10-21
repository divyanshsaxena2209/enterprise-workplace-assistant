from types import SimpleNamespace

import pytest

from app.core.exceptions import ConflictError
from app.repositories.cognito_identity_repository import CognitoIdentityRepository


class FakeQuery:
    def __init__(self, table):
        self.table_state = table
        self.action = "select"
        self.fields = "*"
        self.filters = {}
        self.payload = None

    def select(self, fields):
        self.fields = fields
        self.action = "select"
        return self

    def eq(self, column, value):
        self.filters[column] = value
        return self

    def limit(self, _count):
        return self

    def insert(self, payload):
        self.action = "insert"
        self.payload = payload
        return self

    def execute(self):
        records = self.table_state.records
        if self.action == "select":
            matches = [
                row for row in records
                if all(row.get(key) == value for key, value in self.filters.items())
            ]
            return SimpleNamespace(data=[
                {field: row[field] for field in self.fields.split(",") if field in row}
                for row in matches[:1]
            ])
        if any(
            row["cognito_sub"] == self.payload["cognito_sub"]
            or row["profile_id"] == self.payload["profile_id"]
            for row in records
        ):
            raise RuntimeError("unique constraint violation")
        records.append(dict(self.payload))
        return SimpleNamespace(data=[dict(self.payload)])


class FakeTable:
    def __init__(self):
        self.records = []

    def table(self, _name):
        return FakeQuery(self)


def test_create_mapping_is_idempotent_for_same_pair():
    client = FakeTable()
    repo = CognitoIdentityRepository(client)

    repo.create_mapping("cognito-sub", "profile-id")
    repo.create_mapping("cognito-sub", "profile-id")

    assert client.records == [{"cognito_sub": "cognito-sub", "profile_id": "profile-id"}]


def test_subject_cannot_be_linked_to_a_different_profile():
    client = FakeTable()
    repo = CognitoIdentityRepository(client)
    repo.create_mapping("cognito-sub", "profile-one")

    with pytest.raises(ConflictError, match="already linked to another profile"):
        repo.create_mapping("cognito-sub", "profile-two")


def test_profile_cannot_be_linked_to_a_different_subject():
    client = FakeTable()
    repo = CognitoIdentityRepository(client)
    repo.create_mapping("subject-one", "profile-id")

    with pytest.raises(ConflictError, match="already linked to a different Cognito identity"):
        repo.create_mapping("subject-two", "profile-id")
