from __future__ import annotations
from fastapi import APIRouter
from core.jobs.runtime import source_repository
from core.source.models import SourceProfile, SourceRequest
from core.source.router import build_source_route_plan

router=APIRouter(prefix="/sources",tags=["sources"])

@router.post("",response_model=SourceProfile)
def register_source(source:SourceProfile)->SourceProfile:
    return source_repository.save(source)

@router.get("",response_model=list[SourceProfile])
def list_sources()->list[SourceProfile]:
    return source_repository.list()

@router.post("/route")
def route_source(request:SourceRequest):
    return build_source_route_plan(request,source_repository.list())
