from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_open_when_key_not_configured():
    assert client.get("/api/v1/competitors").status_code == 200


def test_key_required_when_configured(monkeypatch):
    monkeypatch.setenv("RIVALRY_API_KEY", "secret")
    assert client.get("/api/v1/competitors").status_code == 401
    assert client.get("/api/v1/competitors", headers={"X-API-Key": "bad"}).status_code == 401
    assert client.get("/api/v1/competitors", headers={"X-API-Key": "secret"}).status_code == 200
    assert client.get("/health").status_code == 200
