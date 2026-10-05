from fastapi import APIRouter

from core.jobs.runtime import competitor_service
from engines.competitor.models import Competitor

router = APIRouter(prefix="/competitors", tags=["competitors"])


@router.get("", response_model=list[Competitor])
def list_competitors() -> list[Competitor]:
    return competitor_service.list()


@router.post("", response_model=Competitor, status_code=201)
def add_competitor(competitor: Competitor) -> Competitor:
    return competitor_service.add(competitor)
