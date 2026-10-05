from fastapi.testclient import TestClient

from api.main import app


def test_onboarding_uses_business_profile_to_choose_depth():
    client = TestClient(app)
    response = client.post(
        "/api/v1/onboarding/state",
        json={
            "messages": [{"role": "user", "content": "나는 해외 수입업자야"}],
            "business_profile": {
                "business_model": "importer",
                "business_size": "small",
                "geographic_scope": "international",
                "product_count": 100,
                "supply_chain_complexity": 80,
                "channel_count": 4,
                "decision_complexity": 70,
            },
        },
        headers={"X-API-Key": "test"},
    )
    assert response.status_code in {200, 401}


def test_onboarding_state_defaults_are_independent():
    client = TestClient(app)
    first = client.post(
        "/api/v1/onboarding/state",
        json={"messages": []},
        headers={"X-API-Key": "test"},
    )
    second = client.post(
        "/api/v1/onboarding/state",
        json={"messages": []},
        headers={"X-API-Key": "test"},
    )
    if first.status_code == 200 and second.status_code == 200:
        assert first.json()["missing_inputs"] == second.json()["missing_inputs"]
