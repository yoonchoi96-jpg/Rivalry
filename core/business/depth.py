from __future__ import annotations

from .models import BusinessProfile, QuestionDepth, QuestionPlan

_SCOPE_SCORES = {
    "local": 0,
    "regional": 10,
    "national": 20,
    "international": 30,
    "global": 35,
}


def _count_score(value: int | None, thresholds: tuple[int, ...], cap: int) -> int:
    if value is None:
        return 0
    return min(cap, sum(value >= threshold for threshold in thresholds) * (cap // len(thresholds)))


def plan_question_depth(profile: BusinessProfile) -> QuestionPlan:
    """Choose onboarding depth from business context, not a fixed questionnaire.

    Unknown values contribute zero. The planner can therefore start shallow and
    deepen only when new evidence makes additional context useful.
    """

    score = profile.complexity
    reasons: list[str] = []
    topics: list[str] = []

    scope = (profile.geographic_scope or "").strip().lower()
    if scope in _SCOPE_SCORES:
        score += _SCOPE_SCORES[scope]
        if _SCOPE_SCORES[scope] >= 20:
            reasons.append("geographic scope increases external factors")
            topics.append("regions and cross-border exposure")

    product_score = _count_score(profile.product_count, (5, 20, 100), 15)
    if product_score:
        score += product_score
        reasons.append("product breadth increases comparison complexity")
        topics.append("products and pricing")

    customer_score = _count_score(profile.customer_count, (100, 1000, 10000), 15)
    if customer_score:
        score += customer_score
        reasons.append("customer scale increases demand complexity")
        topics.append("customers and demand")

    if profile.supply_chain_complexity:
        score += round(profile.supply_chain_complexity * 0.20)
        reasons.append("supply-chain complexity affects causal analysis")
        topics.append("suppliers and inputs")

    score += min(10, profile.channel_count * 2)
    if profile.channel_count >= 3:
        reasons.append("multiple channels increase operating complexity")
        topics.append("sales and delivery channels")

    score += round(profile.organization_complexity * 0.10)
    if profile.organization_complexity >= 40:
        reasons.append("organizational complexity increases decision paths")
        topics.append("organization and responsibilities")

    score += round(profile.decision_complexity * 0.20)
    if profile.decision_complexity >= 40:
        reasons.append("decision complexity requires deeper business context")
        topics.append("decision criteria and constraints")

    score = min(100, max(0, score))

    if score < 20:
        depth = QuestionDepth.LEVEL_1
    elif score < 35:
        depth = QuestionDepth.LEVEL_2
    elif score < 50:
        depth = QuestionDepth.LEVEL_3
    elif score < 65:
        depth = QuestionDepth.LEVEL_4
    elif score < 80:
        depth = QuestionDepth.LEVEL_5
    elif score < 92:
        depth = QuestionDepth.LEVEL_6
    else:
        depth = QuestionDepth.LEVEL_7

    if not reasons:
        reasons.append("insufficient context; start with the smallest useful question")
    if not topics:
        topics.append("business identity")

    return QuestionPlan(
        depth=depth,
        score=score,
        rationale=reasons,
        next_topics=list(dict.fromkeys(topics)),
    )
