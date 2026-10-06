from fastapi.testclient import TestClient

from api.main import app
from api.routes import businesses as businesses_route
from core.business.repository import InMemoryBusinessRepository


def test_create_and_get_business_entity():
    original = businesses_route.business_repository
    businesses_route.business_repository = InMemoryBusinessRepository()
    try:
        client = TestClient(app)
        payload = {
            "id": "biz-1",
            "name": "Example Coffee",
            "country_code": "KR",
            "business_type": "cafe",
            "channel": "local",
            "goal": "improve margin",
        }
        created = client.post("/api/v1/businesses", json=payload)
        loaded = client.get("/api/v1/businesses/biz-1")
    finally:
        businesses_route.business_repository = original

    assert created.status_code == 201
    assert loaded.status_code == 200
    assert loaded.json()["id"] == "biz-1"
    assert loaded.json()["goal"] == "improve margin"


def test_create_business_rejects_duplicate_id():
    original = businesses_route.business_repository
    businesses_route.business_repository = InMemoryBusinessRepository()
    try:
        client = TestClient(app)
        payload = {
            "id": "biz-1",
            "name": "Example",
            "country_code": "KR",
            "business_type": "service",
            "channel": "local",
        }
        assert client.post("/api/v1/businesses", json=payload).status_code == 201
        duplicate = client.post("/api/v1/businesses", json=payload)
    finally:
        businesses_route.business_repository = original

    assert duplicate.status_code == 409


def test_get_business_returns_404_when_missing():
    original = businesses_route.business_repository
    businesses_route.business_repository = InMemoryBusinessRepository()
    try:
        response = TestClient(app).get("/api/v1/businesses/missing")
    finally:
        businesses_route.business_repository = original

    assert response.status_code == 404
