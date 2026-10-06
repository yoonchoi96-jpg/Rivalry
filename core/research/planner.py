from __future__ import annotations

from core.causal.models import CausalMap, CausalRelation
from core.research.models import ResearchMethod, ResearchPlan, ResearchTask


def build_research_plan(causal_map: CausalMap) -> ResearchPlan:
    tasks: list[ResearchTask] = []

    for factor in causal_map.factors:
        method = ResearchMethod.WEB
        freshness = 1440

        if factor.relation == CausalRelation.DOWNSTREAM:
            method = ResearchMethod.INTERNAL_DATA
            freshness = 60
        elif factor.relation == CausalRelation.UPSTREAM:
            method = ResearchMethod.API
            freshness = 1440

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
