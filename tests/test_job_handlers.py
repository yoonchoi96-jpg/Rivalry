from core.jobs.handlers import JobHandlers
from core.jobs.models import Job, JobType


def test_intelligence_handler_builds_report():
    job = Job(type=JobType.PROCESS_INTELLIGENCE, payload={
        "change": {
            "id": "ch1", "competitor_id": "c1", "type": "PRICE_CHANGED",
            "magnitude": 40, "impact_score": 0, "confidence": 80,
            "detected_at": "2026-10-04T00:00:00+00:00", "source": "test",
        },
        "market_relevance": 80,
        "competitor_importance": 90,
    })
    result = JobHandlers().process_intelligence(job)
    assert result["change_id"] == "ch1"
    assert result["hypotheses"]
    assert result["confidence"] >= 0


def test_intelligence_handler_requires_change():
    job = Job(type=JobType.PROCESS_INTELLIGENCE)
    try:
        JobHandlers().process_intelligence(job)
    except ValueError as exc:
        assert "payload.change" in str(exc)
    else:
        raise AssertionError("expected ValueError")
