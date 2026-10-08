import os

import pytest

from core.intelligence.models import Change, Prediction, Review
from core.intelligence.postgres_repository import PostgresIntelligenceRepository


def test_postgres_repository_has_full_repository_contract():
    repository = PostgresIntelligenceRepository(
        "postgresql://unused",
        connect=lambda *_args, **_kwargs: None,
    )
    assert all(
        hasattr(repository, name)
        for name in (
            "record_changes",
            "record_reviews",
            "record_prediction",
            "record_alert",
            "record_snapshot",
            "latest_snapshot",
            "record_cost_signals",
            "all_changes",
            "all_reviews",
            "all_predictions",
            "all_cost_signals",
            "all_alerts",
        )
    )


def test_postgres_repository_serializes_model_fields():
    change = Change(
        id="ch1",
        competitor_id="c1",
        type="PRICE_CHANGED",
        before=100,
        after=110,
        detected_at="2026-10-04T00:00:00Z",
    )
    row = PostgresIntelligenceRepository._change_row(change)
    assert row["id"] == "ch1"
    assert row["business_id"] is None
    assert row["before_json"].obj == 100
    assert row["after_json"].obj == 110


@pytest.mark.integration
def test_postgres_round_trip_when_database_is_configured():
    dsn = os.getenv("RIVALRY_TEST_DATABASE_URL")
    if not dsn:
        pytest.skip("RIVALRY_TEST_DATABASE_URL is not configured")

    from db.migrate import migrate

    migrate(dsn)
    repository = PostgresIntelligenceRepository(dsn)

    change = Change(
        id="integration-change",
        business_id="b1",
        competitor_id="integration-c1",
        type="PRICE_CHANGED",
        before=100,
        after=110,
        magnitude=10,
        detected_at="2026-10-04T00:00:00Z",
    )
    review = Review(
        id="integration-review",
        competitor_id="integration-c1",
        rating=4.5,
        text="good",
        created_at="2026-10-04T00:00:00Z",
        topics=["taste"],
        product_id="p1",
        confidence=90,
    )
    prediction = Prediction(
        id="integration-prediction",
        competitor_id="integration-c1",
        prediction_type="price_change",
        predicted_at="2026-10-04T00:00:00Z",
        expected_window_days=7,
        probability=75,
        evidence_change_ids=["integration-change"],
    )

    repository.record_changes([change])
    repository.record_reviews([review])
    repository.record_prediction(prediction)
    repository.record_snapshot("integration-c1", {"prices": [110]})
    repository.record_alert({
        "id": "integration-alert",
        "change_id": "integration-change",
        "competitor_id": "integration-c1",
        "recommended_action": "monitor",
    })
    repository.record_alert({
        "id": "integration-alert",
        "change_id": "integration-change",
        "competitor_id": "integration-c1",
        "recommended_action": "review",
    })

    assert repository.all_changes()[0].id == change.id
    assert repository.all_reviews()[0].product_id == "p1"
    assert repository.all_predictions()[0].evidence_change_ids == ["integration-change"]
    assert repository.latest_snapshot("integration-c1") == {"prices": [110]}
    alerts = repository.all_alerts()
    assert len(alerts) == 1
    assert alerts[0]["id"] == "integration-alert"
    assert alerts[0]["recommended_action"] == "review"
