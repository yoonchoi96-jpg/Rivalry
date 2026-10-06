from __future__ import annotations

from .models import SourceProfile, SourceRequest, SourceRoute, SourceRoutePlan


def _score(source: SourceProfile, request: SourceRequest) -> tuple[float, list[str]]:
    reasons: list[str] = []
    if source.reliability < request.minimum_reliability:
        return 0.0, ["below minimum reliability"]

    score = (
        source.reliability * 0.30
        + source.coverage * 0.20
        + source.normalization_quality * 0.15
        + (1 - source.cost) * 0.15
        + (1 - source.latency) * 0.10
    )

    if request.freshness_minutes is not None and source.freshness_minutes is not None:
        if source.freshness_minutes <= request.freshness_minutes:
            score += 0.10
            reasons.append("meets freshness budget")
        else:
            score -= 0.15
            reasons.append("misses freshness budget")
    elif request.freshness_minutes is not None:
        reasons.append("freshness unknown")

    missing = [c for c in request.required_capabilities if c not in source.capabilities]
    if missing:
        return 0.0, [f"missing capability: {c}" for c in missing]

    if source.reliability >= 0.8:
        reasons.append("high reliability")
    if source.normalization_quality >= 0.8:
        reasons.append("high normalization quality")
    return max(0.0, min(1.0, score)), reasons


def build_source_route_plan(
    request: SourceRequest,
    sources: list[SourceProfile],
) -> SourceRoutePlan:
    routes = []
    for source in sources:
        score, rationale = _score(source, request)
        if score > 0:
            routes.append(SourceRoute(source_id=source.id, score=score, rationale=rationale))
    routes.sort(key=lambda route: route.score, reverse=True)
    return SourceRoutePlan(request=request, routes=routes)
