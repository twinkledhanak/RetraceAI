from fastapi.testclient import TestClient

from retraceai.main import app

client = TestClient(app)


def test_search_returns_dummy_results():
    response = client.post("/search", json={"query": "how do I upgrade python"})
    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "how do I upgrade python"
    assert body["results"][0]["title"] == "(placeholder search results)"


def test_search_rejects_empty_query():
    response = client.post("/search", json={"query": ""})
    assert response.status_code == 422
