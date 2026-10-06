from core.impact.models import BusinessImpact
from core.impact.scorer import score_impact
from core.relevance.models import RelevanceProfile, rank_relevance
from core.relevance.scorer import score_impact_relevance


def test_impact_score_uses_exposure_and_significance():
    impact=BusinessImpact(
        id="i1",business_id="b1",entity_id="e1",signal_id="s1",factor_key="fx.exposure",
        exposure=.8,magnitude=.5,confidence=.9,significance=.9,
    )
    assert score_impact(impact) == .36


def test_relevance_priority_is_multiplicative():
    assert rank_relevance(relevance=.8,impact=.5,confidence=.9) == .36


def test_business_factor_weight_changes_priority():
    impact=BusinessImpact(
        id="i2",business_id="b1",entity_id="e1",signal_id="s1",factor_key="labor.wage_pressure",
        exposure=.5,magnitude=.8,confidence=.8,significance=1,
    )
    profile=RelevanceProfile(business_id="b1",factor_weights={"labor.wage_pressure":.2})
    score=score_impact_relevance(impact,profile)
    assert score.relevance == .2
    assert score.priority == .0512
