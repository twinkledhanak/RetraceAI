from datetime import datetime

from bson import ObjectId
from fastapi.testclient import TestClient

import retraceai.api.search
from retraceai.gemini import parse_search_decision
from retraceai.main import app
from retraceai.vector_search import (
    make_json_safe,
    search_upgrade_sessions,
    vector_search_error_message,
)

client = TestClient(app)

DUMMY_DOCS = [
    {
        "_id": "1",
        "sessionId": "s1",
        "appVersion": {"from": "v1", "to": "v2"},
        "status": "resolved",
        "score": 0.92,
    },
    {
        "_id": "2",
        "sessionId": "s2",
        "appVersion": {"from": "v1", "to": "v3"},
        "status": "failed",
        "score": 0.88,
    },
]


def _decide(q, decision):
    return lambda query: (decision, "test")


def test_search_returns_results_when_search_needed(monkeypatch):
    monkeypatch.setattr(retraceai.api.search, "needs_vector_search", _decide("q", True))
    monkeypatch.setattr(retraceai.api.search, "search_upgrade_sessions", lambda q: DUMMY_DOCS)
    response = client.post("/search", json={"query": "how do I upgrade python"})
    assert response.status_code == 200
    body = response.json()
    assert body["needs_vector_search"] is True
    assert body["results"][0]["score"] == 0.92
    assert body["results"][0]["document"]["sessionId"] == "s1"


def test_search_returns_no_results_when_search_not_needed(monkeypatch):
    monkeypatch.setattr(retraceai.api.search, "needs_vector_search", _decide("q", False))
    response = client.post("/search", json={"query": "what is the capital of France"})
    assert response.status_code == 200
    body = response.json()
    assert body["needs_vector_search"] is False
    assert body["results"] == []


def test_search_rejects_empty_query():
    response = client.post("/search", json={"query": ""})
    assert response.status_code == 422


def test_search_503_when_vector_search_fails(monkeypatch):
    monkeypatch.setattr(retraceai.api.search, "needs_vector_search", _decide("q", True))
    boom = lambda q: (_ for _ in ()).throw(RuntimeError("boom"))  # noqa: E731
    monkeypatch.setattr(retraceai.api.search, "search_upgrade_sessions", boom)
    response = client.post("/search", json={"query": "how do I upgrade"})
    assert response.status_code == 503


def test_parse_search_decision_yes():
    assert parse_search_decision('{"needs_vector_search": true, "reason": "upgrade question"}') == (
        True,
        "upgrade question",
    )


def test_parse_search_decision_no():
    assert parse_search_decision('{"needs_vector_search": false, "reason": "general fact"}') == (
        False,
        "general fact",
    )


def test_parse_search_decision_defaults_on_malformed_json():
    assert parse_search_decision("not json at all")[0] is True


def test_search_upgrade_sessions_uses_auto_embedding(monkeypatch):
    captured = {}

    class FakeCollection:
        def aggregate(self, pipeline, **kwargs):
            captured["pipeline"] = pipeline
            return iter([{"_id": "1", "sessionId": "s1", "status": "resolved", "score": 0.95}])

    class FakeDB:
        def __getitem__(self, name):
            return FakeCollection()

    monkeypatch.setattr("retraceai.vector_search.get_database", lambda: FakeDB())
    docs = search_upgrade_sessions("tailwindcss oklch error")
    assert docs == [{"_id": "1", "sessionId": "s1", "status": "resolved", "score": 0.95}]

    vector_stage = captured["pipeline"][0]["$vectorSearch"]
    assert vector_stage["query"] == "tailwindcss oklch error"
    assert "queryVector" not in vector_stage
    assert vector_stage["path"] == "attempts.errorText"


def test_make_json_safe_converts_bson_types():
    doc = {
        "_id": ObjectId("6a7e37d37054b562fc1d5a66"),
        "when": datetime(2026, 8, 13),
        "attempts": [{"errorText": "oklch error", "raw": b"bytes"}],
        "nested": {"flag": True, "count": 3},
    }
    safe = make_json_safe(doc)
    assert safe["_id"] == "6a7e37d37054b562fc1d5a66"
    assert safe["when"] == "2026-08-13T00:00:00"
    assert safe["attempts"][0]["raw"] == "bytes"
    assert safe["nested"] == {"flag": True, "count": 3}


def test_vector_search_error_message():
    from pymongo.errors import OperationFailure

    from retraceai.config import get_settings

    class FakeOpFailure(OperationFailure):
        def __init__(self):
            super().__init__("fake", details={"ok": 0, "code": 8000})

    message = vector_search_error_message(FakeOpFailure())
    assert get_settings().vector_index_name in message
    assert "8000" in message
