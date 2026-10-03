from engines.review.models import Review, Sentiment
from engines.review.service import ReviewIntelligenceService

def test_review_summary():
    reviews=[Review(id="1",competitor_id="c",text="great",created_at="2026-10-04",sentiment=Sentiment.POSITIVE,topics=["service"]), Review(id="2",competitor_id="c",text="bad",created_at="2026-10-04",sentiment=Sentiment.NEGATIVE,topics=["waiting"])]
    out=ReviewIntelligenceService().summarize(reviews)
    assert out["positive_count"] == 1 and out["negative_count"] == 1
