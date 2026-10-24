from importlib import import_module
from types import ModuleType, SimpleNamespace
import sys

import pytest
from fastapi import HTTPException



@pytest.mark.parametrize("owns_session", [True, False])
def test_query_checks_session_ownership_before_writing_any_messages(
    monkeypatch, owns_session
):
    events = []
    rag_module = ModuleType("app.services.knowledge_rag")

    def get_session_messages(session_id, user_id):
        events.append(("ownership_check", session_id, user_id))
        if not owns_session:
            raise Exception("Session not found or unauthorized")
        return [{"role": "user", "content": "previous question"}]

    def add_message(session_id, role, content, sources=None):
        events.append(("message", session_id, role, content, sources))

    def retrieve_and_answer(question, *, k, chat_history):
        events.append(("retrieve", question, k, chat_history))
        return {"answer": "safe answer", "sources": []}

    rag_module.retrieve_and_answer = retrieve_and_answer
    rag_module.process_and_store_document = lambda *_args, **_kwargs: {}
    monkeypatch.setitem(sys.modules, "app.services.knowledge_rag", rag_module)
    # Import only after the stub is installed; otherwise importing the router
    # loads the full document/LLM dependency graph in this lightweight test job.
    sys.modules.pop("app.routers.knowledge", None)
    knowledge = import_module("app.routers.knowledge")

    monkeypatch.setattr(
        knowledge.knowledge_chat_service, "get_session_messages", get_session_messages
    )
    monkeypatch.setattr(knowledge.knowledge_chat_service, "add_message", add_message)

    query = knowledge.QueryRequest(question="new question", session_id="session-123")
    current_user = SimpleNamespace(id="employee-123")

    if not owns_session:
        with pytest.raises(HTTPException) as error:
            knowledge.query_documents(query, current_user)

        assert error.value.status_code == 404
        assert events == [
            ("ownership_check", "session-123", "employee-123")
        ]
        return

    result = knowledge.query_documents(query, current_user)

    assert result == {"answer": "safe answer", "sources": []}
    assert [event[0] for event in events] == [
        "ownership_check",
        "message",
        "retrieve",
        "message",
    ]
    assert events[1] == ("message", "session-123", "user", "new question", None)
    # The new prompt is not duplicated in prior-turn history.
    assert events[2] == (
        "retrieve",
        "new question",
        15,
        [{"role": "user", "content": "previous question"}],
    )
    assert events[3] == (
        "message",
        "session-123",
        "assistant",
        "safe answer",
        [],
    )
