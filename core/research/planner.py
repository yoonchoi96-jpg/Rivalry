from __future__ import annotations

from core.causal.models import CausalMap, CausalRelation
from core.research.models import ResearchMethod, ResearchPlan, ResearchTask
from core.source.models import SourceProfile, SourceRequest
from core.source.router import build_source_route_plan


def build_research_plan(
    causal_map: CausalMap,
    *,
    sources: list[SourceProfile] | None = None,
) -> ResearchPlan:
    tasks: list[ResearchTask] = []

    for factor in causal_map.factors:
        freshness = 60 if factor.relation == CausalRelation.DOWNSTREAM else 1440
        default_method = (
            ResearchMethod.INTERNAL_DATA
            if factor.relation == CausalRelation.DOWNSTREAM
            else ResearchMethod.API
            if factor.relation == CausalRelation.UPSTREAM
            else ResearchMethod.WEB
        )

        method = default_method
        if sources:
            route = build_source_route_plan(
                SourceRequest(metric=factor.key, freshness_minutes=freshness),
                sources,
            )
            if route.routes:
                method = ResearchMethod(route.routes[0].kind.value)
            else:
                method = default_method

        tasks.append(
            ResearchTask(
                factor_key=factor.key,
                objective=f"검증: {factor.label}이(가) 질문에 미치는 영향",
                method=method,
                priority=factor.priority,
                freshness_minutes=freshness,
            )
        )

    tasks.sort(key=lambda item: item.priority, reverse=True)
    return ResearchPlan(question=causal_map.question, tasks=tasks)
