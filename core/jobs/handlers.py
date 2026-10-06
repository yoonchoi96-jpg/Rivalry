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
from core.intelligence.engine import IntelligenceStore
from core.research.executor import ResearchExecutor
from core.decision.engine import DecisionEngine
from core.decision.models import DecisionPolicy, DecisionRecommendation
from core.decision.recommendation_repository import InMemoryDecisionRecommendationRepository
from core.impact.repository import InMemoryImpactRepository
from core.action.dispatcher import ActionDispatcher
from core.evidence.models import AccessMethod, KnowledgeKind
from core.observation.models import Observation
from hashlib import sha256

from .models import Job, JobType
from .pipeline import detect_changes, normalize_collection


class JobHandlers:
    """Application handlers kept independent from the queue implementation."""

    def __init__(self, intelligence: IntelligenceService | None = None, adapters: AdapterRegistry | None = None, recommendations: RecommendationService | None = None, reviews: ReviewIntelligenceService | None = None, store: IntelligenceStore | None = None, research: ResearchExecutor | None = None, impact_repository=None, decision_policies=None, decision_recommendations=None, signal_repository=None, observation_repository=None) -> None:
        self.intelligence = intelligence or IntelligenceService()
        self.adapters = adapters or AdapterRegistry()
        if adapters is None:
            from adapters.open_food_facts import OpenFoodFactsAdapter
            self.adapters.register("GLOBAL", "openfoodfacts", OpenFoodFactsAdapter())
        self.recommendations = recommendations or RecommendationService()
        self.reviews = reviews or ReviewIntelligenceService()
        self.store = store or IntelligenceStore()
        self.research = research
        self.impact_repository = impact_repository or InMemoryImpactRepository()
        self.decision_policies = decision_policies
        self.decision_recommendations = decision_recommendations or InMemoryDecisionRecommendationRepository()
        self.signal_repository = signal_repository
        self.observation_repository = observation_repository


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
        before = self.store.latest_snapshot(competitor_id) or {"prices": [], "products": []}
        changes = detect_changes(competitor_id, before, normalized, source=str(platform), business_id=str(competitor.get("business_id") or "") or None)
        self.store.record_snapshot(competitor_id, normalized)
        typed_reviews = [Review.model_validate(item) for item in normalized["reviews"] if isinstance(item, dict)]
        self.store.record_changes(changes)
        self.store.record_reviews(typed_reviews)
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
        alert = {"change_id": str(change.get("id", "")), "competitor_id": str(change.get("competitor_id", "")), "type": str(change.get("type", "UNKNOWN")), "impact_score": float(change.get("impact_score", 0)), "confidence": float(intelligence.get("confidence", 0)), "summary": str(intelligence.get("summary", "Material competitor change detected.")), "likely_cause": top_cause, "recommended_action": recommendation.get("action", "monitor") if isinstance(recommendation, dict) else "monitor"}
        self.store.record_alert(alert)
        return alert

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
        historical = self.store.competitor_history(competitor_id, days=30)
        combined = historical + [change for change in typed if change.id not in {item.id for item in historical}]
        counts: dict[str, int] = {}
        evidence_by_type: dict[str, list[str]] = {}
        for change in combined:
            counts[change.type] = counts.get(change.type, 0) + 1
            evidence_by_type.setdefault(change.type, []).append(change.id)
        repeated = max(counts.items(), key=lambda item: item[1], default=(None, 0))
        if repeated[0] is None or repeated[1] < 2:
            return {"prediction": None, "reason": "insufficient repeated change evidence"}
        evidence = evidence_by_type[repeated[0]]
        prediction = Prediction(id=str(uuid4()), competitor_id=competitor_id, prediction_type=f"repeat_{repeated[0].lower()}", predicted_at=datetime.now(timezone.utc).isoformat(), expected_window_days=7, probability=min(95, 55 + repeated[1] * 10), evidence_change_ids=evidence)
        self.store.record_prediction(prediction)
        return {"prediction": prediction.model_dump(mode="json")}

    def generate_decision(self, job: Job) -> dict[str, object]:
        impact_id = job.payload.get("impact_id")
        policy_id = job.payload.get("policy_id")
        if not isinstance(impact_id, str) or not impact_id:
            raise ValueError("generate_decision requires payload.impact_id")
        if not isinstance(policy_id, str) or not policy_id:
            raise ValueError("generate_decision requires payload.policy_id")
        if self.decision_policies is None:
            raise RuntimeError("decision policy registry is not configured")
        impact = self.impact_repository.get(impact_id)
        if impact is None:
            raise ValueError(f"business impact not found: {impact_id}")
        policy = self.decision_policies.get(policy_id)
        if policy is None:
            raise ValueError(f"decision policy not found: {policy_id}")
        if self.signal_repository is None:
            raise RuntimeError("signal repository is not configured")
        signal = self.signal_repository.get(impact.signal_id)
        if signal is None:
            raise ValueError(f"signal not found: {impact.signal_id}")
        recommendation = DecisionEngine().recommend(impact, signal, policy)
        stored = self.decision_recommendations.save(recommendation)
        return {"recommendation": stored.model_dump(mode="json")}

    def dispatch_action(self, job: Job) -> dict[str, object]:
        raw = job.payload.get("recommendation")
        if not isinstance(raw, dict):
            raise ValueError("dispatch_action requires payload.recommendation")
        recommendation = DecisionRecommendation.model_validate(raw)
        action = ActionDispatcher().dispatch(recommendation)
        impact = self.impact_repository.get(recommendation.impact_id)
        alert = {
            "id": f"recommendation:{recommendation.impact_id}",
            "change_id": recommendation.impact_id,
            "competitor_id": recommendation.business_id,
            "type": "DECISION_RECOMMENDATION",
            "impact_score": (impact.magnitude * impact.exposure * 100) if impact is not None else recommendation.priority * 100,
            "confidence": recommendation.confidence * 100,
            "summary": recommendation.rationale,
            "likely_cause": recommendation.factor_key,
            "recommended_action": recommendation.action,
            "action_kind": action.kind.value,
            "recommendation_id": action.recommendation_id,
            "signal_id": action.signal_id,
            "policy_id": action.policy_id,
            "follow_up_job": action.follow_up_job.value if action.follow_up_job else None,
        }
        self.store.record_alert(alert)
        return {"action": action.model_dump(mode="json"), "alert": alert}


    def ingest_research(self, job: Job) -> dict[str, object]:
        raw = job.payload.get("research")
        if not isinstance(raw, dict):
            raise ValueError("ingest_research requires payload.research")
        observations = []
        for item in raw.get("tasks", []):
            if not isinstance(item, dict) or not isinstance(item.get("evidence"), dict):
                continue
            evidence = item["evidence"]
            entity_id = str(job.payload.get("business_id") or "")
            if not entity_id:
                continue
            structured = evidence.get("observation") if isinstance(evidence.get("observation"), dict) else {}
            observed_at = structured.get("observed_at") or evidence.get("captured_at")
            normalized = structured.get("normalized_value")
            observation = Observation(
                id=sha256(str(evidence.get("id", "")).encode()).hexdigest()[:32],
                entity_id=entity_id,
                entity_type="business",
                metric=str(item.get("factor_key") or "research_evidence"),
                raw_value=structured.get("raw_value", evidence.get("statement")),
                normalized_value=float(normalized) if isinstance(normalized, (int, float)) else None,
                unit=str(structured.get("unit")) if structured.get("unit") else None,
                currency=str(structured.get("currency")) if structured.get("currency") else None,
                geography=str(structured.get("geography")) if structured.get("geography") else None,
                observed_at=str(observed_at or ""),
                source_id=str(item.get("source_id") or evidence.get("source_id") or ""),
                evidence_id=str(evidence.get("id") or ""),
                access_method=AccessMethod.WEB,
                confidence=float(evidence.get("confidence", 0.5)),
                knowledge_kind=KnowledgeKind.FACT,
                provenance={"research_question": raw.get("question"), "research_factor": item.get("factor_key"), "structured": bool(structured)},
            )
            self.observation_repository.save(observation)
            observations.append(observation.model_dump(mode="json"))
        return {"observations": observations, "observation_count": len(observations)}

    def execute_research(self, job: Job) -> dict[str, object]:
        if self.research is None:
            raise RuntimeError("research executor is not configured")
        plan = job.payload.get("plan")
        if not isinstance(plan, dict):
            raise ValueError("execute_research requires payload.plan")
        from core.research.models import ResearchPlan
        return self.research.execute(ResearchPlan.model_validate(plan))

    def registry(self) -> dict[JobType, Any]:
        return {JobType.COLLECT_COMPETITOR: self.collect_competitor, JobType.PROCESS_INTELLIGENCE: self.process_intelligence, JobType.BUILD_ALERT: self.build_alert, JobType.ANALYZE_REVIEWS: self.analyze_reviews, JobType.GENERATE_PREDICTION: self.generate_prediction, JobType.EXECUTE_RESEARCH: self.execute_research, JobType.INGEST_RESEARCH: self.ingest_research, JobType.GENERATE_DECISION: self.generate_decision, JobType.DISPATCH_ACTION: self.dispatch_action}
