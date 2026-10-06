from __future__ import annotations

from core.impact.models import BusinessImpact
from core.impact.scorer import score_impact
from core.qa.engine import validate_signal
from core.signal.models import Signal

from .models import DecisionPolicy, DecisionRecommendation


class DecisionEngine:
    def recommend(
        self,
        impact: BusinessImpact,
        signal: Signal,
        policy: DecisionPolicy,
    ) -> DecisionRecommendation:
        if impact.entity_id != signal.entity_id:
            raise ValueError("impact and signal entity lineage does not match")
        if impact.signal_id != signal.id:
            raise ValueError("impact signal_id does not match signal")

        qa = validate_signal(signal)
        if qa.status.value == "fail":
            raise ValueError(f"signal QA failed: {', '.join(qa.issues)}")

        if impact.observation_ids != signal.observation_ids:
            raise ValueError("impact observation lineage must match signal lineage")
        if impact.measurement_ids != signal.measurement_ids:
            raise ValueError("impact measurement lineage must match signal lineage")

        impact_score = score_impact(impact)
        rule = next(
            (
                candidate
                for candidate in policy.rules
                if candidate.factor_key in (impact.factor_key, "*")
                and candidate.min_impact <= impact_score <= candidate.max_impact
            ),
            None,
        )

        action = rule.action if rule else policy.default_action
        rationale = rule.rationale if rule else policy.default_rationale
        confidence = round(min(impact.confidence, signal.confidence, qa.score), 10)
        priority = round(impact_score * confidence, 10)

        return DecisionRecommendation(
            business_id=impact.business_id,
            impact_id=impact.id,
            action=action,
            priority=priority,
            rationale=rationale,
            confidence=confidence,
            signal_id=signal.id,
            factor_key=impact.factor_key,
        )
