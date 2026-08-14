from bson import ObjectId
from fastapi.testclient import TestClient

from retraceai.main import app

client = TestClient(app)

PAYLOAD = {
    "sessionId": "s2",
    "appVersion": {"from": "v2", "to": "v3"},
    "status": "resolved",
    "attempts": [
        {
            "library": "vite",
            "action": "upgrade",
            "fromVersion": "4.0.0",
            "toVersion": "5.0.0",
            "succeeded": True,
            "notes": "swapped rollup config to rolldown",
        }
    ],
    "coupledWith": ["vite", "vitest"],
}


def test_create_session_writes_to_atlas(monkeypatch):
    created_doc = {**PAYLOAD, "_id": ObjectId("6a7e37d37054b562fc1d5a66")}

    class FakeCollection:
        def insert_one(self, payload):
            self._inserted = payload
            return type("Result", (), {"inserted_id": created_doc["_id"]})()

        def find_one(self, filter):
            return created_doc

    class FakeDB:
        def __getitem__(self, name):
            return FakeCollection()

    monkeypatch.setattr("retraceai.api.sessions.get_database", lambda: FakeDB())
    response = client.post("/sessions", json=PAYLOAD)
    assert response.status_code == 201
    body = response.json()
    assert body["_id"] == "6a7e37d37054b562fc1d5a66"
    assert body["sessionId"] == "s2"
    assert body["attempts"][0]["library"] == "vite"


def test_create_session_defaults_timestamp(monkeypatch):
    captured = {}

    class FakeCollection:
        def insert_one(self, payload):
            captured["payload"] = payload
            return type("Result", (), {"inserted_id": ObjectId()})()

        def find_one(self, filter):
            return captured["payload"]

    class FakeDB:
        def __getitem__(self, name):
            return FakeCollection()

    monkeypatch.setattr("retraceai.api.sessions.get_database", lambda: FakeDB())
    response = client.post("/sessions", json=PAYLOAD)
    assert response.status_code == 201
    assert captured["payload"]["timestamp"]


def test_create_session_validates_schema():
    response = client.post("/sessions", json={"sessionId": "s3"})
    assert response.status_code == 422


NEW_ATTEMPT = {
    "library": "vite",
    "action": "downgrade",
    "fromVersion": "5.0.0",
    "toVersion": "4.0.0",
    "succeeded": False,
    "errorText": "rolldown missing plugin",
}


def test_add_attempt_appends_and_returns_updated_doc(monkeypatch):
    appended_attempt = {**NEW_ATTEMPT, "errorText": "rolldown missing plugin"}
    updated = {**PAYLOAD, "attempts": [PAYLOAD["attempts"][0], appended_attempt]}

    def fake_write(session_id, attempt):
        assert session_id == PAYLOAD["sessionId"]
        return updated

    monkeypatch.setattr("retraceai.api.sessions.add_attempt_to_session", fake_write)
    response = client.post(f"/sessions/{PAYLOAD['sessionId']}/attempts", json=NEW_ATTEMPT)
    assert response.status_code == 200
    body = response.json()
    assert len(body["attempts"]) == 2
    assert body["attempts"][-1]["errorText"] == "rolldown missing plugin"


def test_add_attempt_404_when_session_missing(monkeypatch):
    def fake_write(session_id, attempt):
        raise KeyError(f"No session found with sessionId={session_id}")

    monkeypatch.setattr("retraceai.api.sessions.add_attempt_to_session", fake_write)
    response = client.post("/sessions/does-not-exist/attempts", json=NEW_ATTEMPT)
    assert response.status_code == 404


def test_add_attempt_503_when_atlas_fails(monkeypatch):
    def fake_write(session_id, attempt):
        raise RuntimeError("Failed to update Atlas: connection lost")

    monkeypatch.setattr("retraceai.api.sessions.add_attempt_to_session", fake_write)
    response = client.post(f"/sessions/{PAYLOAD['sessionId']}/attempts", json=NEW_ATTEMPT)
    assert response.status_code == 503
