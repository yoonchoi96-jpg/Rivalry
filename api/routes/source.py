from fastapi import APIRouter
from core.source.models import SourceProfile, SourceRequest, SourceRoutePlan
from core.source.router import build_source_route_plan

router=APIRouter(prefix="/sources",tags=["sources"])

@router.post("/route",response_model=SourceRoutePlan)
def route_sources(request: SourceRequest, sources: list[SourceProfile]):
    return build_source_route_plan(request, sources)
