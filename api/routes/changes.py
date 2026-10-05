from fastapi import APIRouter

from core.jobs.runtime import intelligence_store
from engines.change_detection.models import Change

router = APIRouter(prefix="/changes", tags=["changes"])


@router.get("", response_model=list[Change])
def list_changes() -> list[Change]:
    return sorted(intelligence_store.changes, key=lambda item: item.impact_score, reverse=True)
