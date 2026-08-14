import pytest

from retraceai.memory import add_attempt_to_session
from tests.test_sessions import NEW_ATTEMPT, PAYLOAD


def test_add_attempt_to_session_appends_and_returns_doc(monkeypatch):
    original = {**PAYLOAD, "attempts": [PAYLOAD["attempts"][0]]}

    class FakeCollection:
        def update_one(self, filter, update):
            if filter["sessionId"] != PAYLOAD["sessionId"]:
                return type("Result", (), {"matched_count": 0})()
            original["attempts"].append(update["$push"]["attempts"])
            return type("Result", (), {"matched_count": 1})()

        def find_one(self, filter):
            return original

    class FakeDB:
        def __getitem__(self, name):
            return FakeCollection()

    monkeypatch.setattr("retraceai.memory.get_database", lambda: FakeDB())
    doc = add_attempt_to_session(PAYLOAD["sessionId"], NEW_ATTEMPT)
    assert len(doc["attempts"]) == 2
    assert doc["attempts"][-1]["errorText"] == "rolldown missing plugin"


def test_add_attempt_to_session_raises_when_session_missing(monkeypatch):
    class FakeCollection:
        def update_one(self, filter, update):
            return type("Result", (), {"matched_count": 0})()

    class FakeDB:
        def __getitem__(self, name):
            return FakeCollection()

    monkeypatch.setattr("retraceai.memory.get_database", lambda: FakeDB())
    with pytest.raises(KeyError, match="No session found"):
        add_attempt_to_session("does-not-exist", NEW_ATTEMPT)


def test_add_attempt_to_session_raises_on_atlas_error(monkeypatch):
    class BoomCollection:
        def update_one(self, filter, update):
            raise RuntimeError("connection lost")

    class FakeDB:
        def __getitem__(self, name):
            return BoomCollection()

    monkeypatch.setattr("retraceai.memory.get_database", lambda: FakeDB())
    with pytest.raises(RuntimeError, match="Failed to update Atlas"):
        add_attempt_to_session(PAYLOAD["sessionId"], NEW_ATTEMPT)
