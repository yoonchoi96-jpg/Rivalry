from fastapi.testclient import TestClient

from api.main import app
from api.routes import businesses as businesses_route
from api.routes import intent as intent_route
from api.routes import research as research_route
from core.business.entity import BusinessEntity
from core.business.repository import InMemoryBusinessRepository


def test_research_plan_is_business_anchored():
    original = businesses_route.business_repository
    repository = InMemoryBusinessRepository()
    repository.save(
        BusinessEntity(
            id="biz-1",
            name="Importer",
            country_code="KR",
            business_type="importer",
            channel="b2b",
        )
    )
    businesses_route.business_repository = repository
    intent_route.business_repository = repository
    research_route.business_repository = repository
    try:
        response = TestClient(app).post(
            "/api/v1/research/plan",
            json={
                "business_id": "biz-1",
                "question": "왜 마진이 떨어졌지?",
                "intent": "explain",
            },
        )
    finally:
        businesses_route.business_repository = original
        intent_route.business_repository = original
        research_route.business_repository = original

    assert response.status_code == 200
    body = response.json()
    assert body["causal_map"]["question"] == "왜 마진이 떨어졌지?"
    assert body["research_plan"]["tasks"]


def test_research_plan_rejects_unknown_business():
    original = businesses_route.business_repository
    repository = InMemoryBusinessRepository()
    businesses_route.business_repository = repository
    intent_route.business_repository = repository
    research_route.business_repository = repository
    try:
        response = TestClient(app).post(
            "/api/v1/research/plan",
            json={"business_id": "missing", "question": "왜?"},
        )
    finally:
        businesses_route.business_repository = original
        intent_route.business_repository = original
        research_route.business_repository = original

    assert response.status_code == 404
