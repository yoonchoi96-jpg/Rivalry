from core.source.models import SourceKind, SourceProfile, SourceRequest
from core.source.router import build_source_route_plan


def test_source_router_prefers_reliable_normalized_source():
    sources = [
        SourceProfile(id="web",name="Web",kind=SourceKind.WEB,reliability=.7,coverage=.9,cost=.1,latency=.2,normalization_quality=.6,freshness_minutes=30),
        SourceProfile(id="api",name="Official API",kind=SourceKind.API,reliability=.95,coverage=.8,cost=.2,latency=.1,normalization_quality=.95,freshness_minutes=10),
    ]
    plan = build_source_route_plan(SourceRequest(metric="price",freshness_minutes=60),sources)
    assert plan.routes[0].source_id == "api"
    assert plan.routes[0].kind == SourceKind.API


def test_source_router_rejects_missing_capability():
    source = SourceProfile(id="s",name="Source",kind=SourceKind.API,capabilities=["price"])
    plan = build_source_route_plan(SourceRequest(metric="price",required_capabilities=["fx"]),[source])
    assert plan.routes == []


def test_research_planner_uses_routed_source():
    from core.business.entity import BusinessEntity
    from core.causal.builder import build_causal_map
    from core.research.models import ResearchMethod
    from core.research.planner import build_research_plan

    business = BusinessEntity(id="b1",name="B",country_code="KR",business_type="x",channel="x")
    causal = build_causal_map("가격 변화", business)
    sources = [
        SourceProfile(id="web-1",name="Web",kind=SourceKind.WEB,reliability=.6,coverage=.6,normalization_quality=.5),
        SourceProfile(id="api-1",name="API",kind=SourceKind.API,reliability=.95,coverage=.9,normalization_quality=.9),
    ]
    plan = build_research_plan(causal, sources=sources)
    assert plan.tasks
    assert plan.tasks[0].method == ResearchMethod.API
