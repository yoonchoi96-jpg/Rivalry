from core.business.entity import BusinessEntity
from core.business.models import BusinessProfile
from core.causal.builder import build_causal_map
from core.causal.models import CausalRelation
from core.intent.models import IntentKind
from core.research.models import ResearchMethod
from core.research.planner import build_research_plan


def test_international_business_prioritizes_fx_and_logistics():
    business = BusinessEntity(
        id="biz-1",
        name="Importer",
        country_code="KR",
        business_type="importer",
        channel="b2b",
        profile=BusinessProfile(
            geographic_scope="international",
            supply_chain_complexity=70,
        ).model_dump(),
    )
    causal_map = build_causal_map(
        "왜 마진이 떨어졌지?",
        business,
        intent=IntentKind.EXPLAIN,
    )
    fx = next(item for item in causal_map.factors if item.key == "fx_logistics")
    assert fx.relation == CausalRelation.UPSTREAM
    assert fx.priority == 95


def test_research_planner_prefers_internal_data_for_outcomes():
    business = BusinessEntity(
        id="biz-1",
        name="Cafe",
        country_code="KR",
        business_type="cafe",
        channel="local",
    )
    plan = build_research_plan(build_causal_map("매출이 왜 떨어졌지?", business))
    outcome = next(item for item in plan.tasks if item.factor_key == "customer_outcome")
    assert outcome.method == ResearchMethod.INTERNAL_DATA
    assert plan.tasks[0].priority >= plan.tasks[-1].priority
