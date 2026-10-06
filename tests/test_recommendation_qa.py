from core.decision.models import DecisionRecommendation
from core.qa.engine import validate_recommendation
from core.qa.models import QAStatus


def test_recommendation_qa_rejects_missing_policy_lineage():
    result = validate_recommendation(
        DecisionRecommendation(
            business_id="b1",
            impact_id="i1",
            action="review",
            priority=0.8,
            rationale="material impact",
            confidence=0.9,
            signal_id="s1",
            factor_key="competitive_price",
        )
    )

    assert result.status == QAStatus.FAIL
    assert "recommendation policy_id is missing" in result.issues


def test_recommendation_qa_passes_complete_lineage():
    result = validate_recommendation(
        DecisionRecommendation(
            business_id="b1",
            impact_id="i1",
            action="review",
            priority=0.8,
            rationale="material impact",
            confidence=0.9,
            signal_id="s1",
            factor_key="competitive_price",
            policy_id="policy-v1",
        )
    )

    assert result.status == QAStatus.PASS
