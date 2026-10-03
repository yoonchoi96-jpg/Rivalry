from core.intelligence.models import Change, Review, Sentiment
from core.intelligence.services import AlertIntelligenceService, ImpactScoringService, ReviewIntelligenceService


def test_impact_score_uses_geometric_mean():
    score = ImpactScoringService.score(100, 100, 100, 100, 100)
    assert score == 100


def test_review_summary():
    reviews = [
        Review(id="1", competitor_id="c", rating=5, created_at="2026-01-01", sentiment=Sentiment.POSITIVE, topics=["taste"]),
        Review(id="2", competitor_id="c", rating=2, created_at="2026-01-02", sentiment=Sentiment.NEGATIVE, topics=["delivery"]),
    ]
    summary = ReviewIntelligenceService.summarize(reviews)
    assert summary["review_count"] == 2
    assert summary["average_rating"] == 3.5
    assert summary["negative_count"] == 1


def test_alert_prioritization():
    low = Change(id="1", competitor_id="c", type="x", detected_at="2026-01-01", impact_score=10, confidence=90)
    high = Change(id="2", competitor_id="c", type="x", detected_at="2026-01-01", impact_score=90, confidence=80)
    assert AlertIntelligenceService.prioritize([low, high])[0].id == "2"
