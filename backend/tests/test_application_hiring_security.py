from types import SimpleNamespace

from app.services.application_service import ApplicationService


class _TableQuery:
    def __init__(self, table_name, rows_by_table):
        self.table_name = table_name
        self.rows_by_table = rows_by_table

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def execute(self):
        return SimpleNamespace(data=self.rows_by_table.get(self.table_name, []))


class _FakeClient:
    def __init__(self):
        self.rows_by_table = {
            "candidates": [{"email": "candidate@example.invalid", "full_name": "Test Candidate"}],
            "jobs": [{"title": "Engineer", "department": "Engineering"}],
            # No profile exists yet, so the hiring flow must provision one.
            "profiles": [],
            # Keep this test focused on account creation, not onboarding seeding.
            "onboarding_templates": [],
        }
        self.created_users = []
        self.auth = SimpleNamespace(
            admin=SimpleNamespace(create_user=self._create_user)
        )

    def table(self, table_name):
        return _TableQuery(table_name, self.rows_by_table)

    def _create_user(self, payload):
        self.created_users.append(payload)
        return SimpleNamespace(user=SimpleNamespace(id="new-profile-id"))


class _FakeApplicationRepository:
    def get_application(self, _application_id):
        return SimpleNamespace(
            application=SimpleNamespace(
                status="Applied",
                candidate_id="candidate-id",
                job_id="job-id",
            )
        )


class _FakePipelineRepository:
    def update_application_status(self, *_args, **_kwargs):
        return None

    def insert_status_history(self, *_args, **_kwargs):
        return None


def test_hiring_provisioning_never_uses_a_shared_default_password():
    client = _FakeClient()
    service = ApplicationService(_FakeApplicationRepository(), client)
    service.pipeline_repo = _FakePipelineRepository()

    # Hiring should provision the account without returning or reusing a default
    # credential. The random password remains solely in the admin-create request.
    service.accept_application("application-id", "manager-id")

    assert len(client.created_users) == 1
    payload = client.created_users[0]
    password = payload["password"]
    assert isinstance(password, str)
    assert len(password) >= 48
    assert password != "Password123!"
    assert payload["email"] == "candidate@example.invalid"
    assert payload["email_confirm"] is True
    assert payload["user_metadata"]["role"] == "EMPLOYEE"
