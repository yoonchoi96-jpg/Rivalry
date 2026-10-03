from fastapi import APIRouter
from engines.competitor.models import Competitor
from engines.competitor.service import CompetitorService
router=APIRouter(prefix="/competitors",tags=["competitors"])
service=CompetitorService()
@router.get("",response_model=list[Competitor])
def list_competitors(): return service.list()
@router.post("",response_model=Competitor,status_code=201)
def add_competitor(competitor:Competitor): return service.add(competitor)
