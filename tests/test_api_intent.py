from fastapi.testclient import TestClient

from api.main import app
from api.routes import businesses as businesses_route
from core.business.entity import BusinessEntity
from core.business.repository import InMemoryBusinessRepository


def test_intent_plan_uses_business_context_before_asking():
    original = businesses_route.business_repository
    repository = InMemoryBusinessRepository()
    repository.save(
        BusinessEntity(
            id="biz-1",
            name="Example Coffee",
            country_code="KR",
            business_type="cafe",
            channel="local",
            goal="improve margin",
        )
    )
    businesses_route.business_repository = repository
    try:
        response = TestClient(app).post(
            "/api/v1/intent/plan",
            json={"business_id": "biz-1", "text": "왜 매출이 떨어졌어?"},
        )
    finally:
        businesses_route.business_repository = original

    assert response.status_code == 200
    body = response.json()
    assert body["kind"] == "explain"
    assert "business identity" in body["known"]
    assert "current goal" in body["known"]
    assert body["required_questions"] == []


def test_intent_plan_requires_existing_business():
    original = businesses_route.business_repository
    businesses_route.business_repository = InMemoryBusinessRepository()
    try:
        response = TestClient(app).post(
            "/api/v1/intent/plan",
            json={"business_id": "missing", "text": "왜 매출이 떨어졌어?"},
        )
    finally:
        businesses_route.business_repository = original

    assert response.status_code == 404
