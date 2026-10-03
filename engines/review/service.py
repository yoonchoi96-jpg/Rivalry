from collections import Counter
from .models import Review, Sentiment

class ReviewIntelligenceService:
    def summarize(self, reviews: list[Review], days: int = 3):
        positive = sum(r.sentiment == Sentiment.POSITIVE for r in reviews)
        negative = sum(r.sentiment == Sentiment.NEGATIVE for r in reviews)
        topics = Counter(topic for r in reviews for topic in r.topics)
        return {"review_count": len(reviews), "positive_count": positive, "negative_count": negative, "top_topics": topics.most_common(10), "window_days": days}
