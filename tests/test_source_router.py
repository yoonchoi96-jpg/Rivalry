from core.source.models import SourceKind, SourceProfile, SourceRequest
from core.source.router import build_source_route_plan


def test_source_router_prefers_reliable_normalized_source():
    sources = [
        SourceProfile(id="web",name="Web",kind=SourceKind.WEB,reliability=.7,coverage=.9,cost=.1,latency=.2,normalization_quality=.6,freshness_minutes=30),
        SourceProfile(id="api",name="Official API",kind=SourceKind.API,reliability=.95,coverage=.8,cost=.2,latency=.1,normalization_quality=.95,freshness_minutes=10),
    ]
    plan = build_source_route_plan(SourceRequest(metric="price",freshness_minutes=60),sources)
    assert plan.routes[0].source_id == "api"


def test_source_router_rejects_missing_capability():
    source = SourceProfile(id="s",name="Source",kind=SourceKind.API,capabilities=["price"])
    plan = build_source_route_plan(SourceRequest(metric="price",required_capabilities=["fx"]),[source])
    assert plan.routes == []
