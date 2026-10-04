from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from adapters.registry import AdapterRegistry
from engines.change_detection.models import Change
from engines.intelligence.service import IntelligenceService
from engines.prediction.models import Prediction
from engines.recommendation.service import RecommendationService
from engines.review.models import Review
from engines.review.service import ReviewIntelligenceService

from .models import Job, JobType
from .pipeline import detect_changes, normalize_collection


class JobHandlers:
    """Application handlers kept independent from the queue implementation."""

    def __init__(self, intelligence: IntelligenceService | None = None, adapters: AdapterRegistry | None = None, recommendations: RecommendationService | None = None, reviews: ReviewIntelligenceService | None = None) -> None:
        self.intelligence = intelligence or IntelligenceService()
        self.adapters = adapters or AdapterRegistry()
        self.recommendations = recommendations or RecommendationService()
        self.reviews = reviews or ReviewIntelligenceService()
        self._snapshots: dict[str, dict[str, object]] = {}

    def collect_competitor(self, job: Job) -> dict[str, object]:
        country = job.payload.get("country_code")
        platform = job.payload.get("platform")
        competitor = job.payload.get("competitor")
        if not all(isinstance(value, str) and value for value in (country, platform)):
            raise ValueError("collect_competitor requires country_code and platform")
        adapter = self.adapters.get(country, platform)
        if adapter is None:
            raise ValueError(f"No adapter registered for {country}/{platform}")
        if not isinstance(competitor, dict):
            raise ValueError("collect_competitor requires payload.competitor")
        data: dict[str, object] = {"competitor": competitor}
        for name, method in (("products", adapter.get_products), ("prices", adapter.get_prices), ("reviews", adapter.get_reviews), ("promotions", adapter.get_promotions)):
            data[name] = method(competitor)
        normalized = normalize_collection(data)
        competitor_id = str(competitor.get("id", ""))
        before = self._snapshots.get(competitor_id, {"prices": [], "products": []})
        changes = detect_changes(competitor_id, before, normalized, source=str(platform))
        self._snapshots[competitor_id] = normalized
        return {**normalized, "changes": [change.model_dump(mode="json") for change in changes]}

    def process_intelligence(self, job: Job) -> dict[str, object]:
        raw_change = job.payload.get("change")
        if not isinstance(raw_change, dict):
            raise ValueError("process_intelligence requires payload.change")
        change = Change.model_validate(raw_change)
        report = self.intelligence.analyze_change(change, market_relevance=float(job.payload.get("market_relevance", 50)), competitor_importance=float(job.payload.get("competitor_importance", 50)), persistence=float(job.payload.get("persistence", 50)), evidence=[str(item) for item in job.payload.get("evidence", []) if isinstance(item, str)])
        recommendation = self.recommendations.recommend(change)
        return {**report.model_dump(mode="json"), "recommendation": recommendation}

    def build_alert(self, job: Job) -> dict[str, object]:
        change = job.payload.get("change")
        intelligence = job.payload.get("intelligence")
        if not isinstance(change, dict) or not isinstance(intelligence, dict):
            raise ValueError("build_alert requires payload.change and payload.intelligence")
        hypotheses = intelligence.get("hypotheses", [])
        top_cause = "unknown"
        if isinstance(hypotheses, list) and hypotheses and isinstance(hypotheses[0], dict):
            top_cause = str(hypotheses[0].get("type", "unknown"))
        recommendation = intelligence.get("recommendation")
        return {"change_id": str(change.get("id", "")), "competitor_id": str(change.get("competitor_id", "")), "type": str(change.get("type", "UNKNOWN")), "impact_score": float(change.get("impact_score", 0)), "confidence": float(intelligence.get("confidence", 0)), "summary": str(intelligence.get("summary", "Material competitor change detected.")), "likely_cause": top_cause, "recommended_action": recommendation.get("action", "monitor") if isinstance(recommendation, dict) else "monitor"}

    def analyze_reviews(self, job: Job) -> dict[str, object]:
        raw_reviews = job.payload.get("reviews", [])
        if not isinstance(raw_reviews, list):
            raise ValueError("analyze_reviews requires payload.reviews")
        reviews = [Review.model_validate(item) for item in raw_reviews if isinstance(item, dict)]
        return self.reviews.summarize(reviews, days=int(job.payload.get("days", 3)))

    def generate_prediction(self, job: Job) -> dict[str, object]:
        changes = job.payload.get("changes", [])
        competitor_id = str(job.payload.get("competitor_id", ""))
        if not isinstance(changes, list):
            raise ValueError("generate_prediction requires payload.changes")
        typed = [Change.model_validate(item) for item in changes if isinstance(item, dict)]
        counts: dict[str, int] = {}
        evidence: list[str] = []
        for change in typed:
            counts[change.type] = counts.get(change.type, 0) + 1
            evidence.append(change.id)
        repeated = max(counts.items(), key=lambda item: item[1], default=(None, 0))
        if repeated[0] is None or repeated[1] < 2:
            return {"prediction": None, "reason": "insufficient repeated change evidence"}
        prediction = Prediction(id=str(uuid4()), competitor_id=competitor_id, prediction_type=f"repeat_{repeated[0].lower()}", predicted_at=datetime.now(timezone.utc).isoformat(), expected_window_days=7, probability=min(95, 55 + repeated[1] * 10), evidence_change_ids=evidence)
        return {"prediction": prediction.model_dump(mode="json")}

    def registry(self) -> dict[JobType, Any]:
        return {JobType.COLLECT_COMPETITOR: self.collect_competitor, JobType.PROCESS_INTELLIGENCE: self.process_intelligence, JobType.BUILD_ALERT: self.build_alert, JobType.ANALYZE_REVIEWS: self.analyze_reviews, JobType.GENERATE_PREDICTION: self.generate_prediction}
