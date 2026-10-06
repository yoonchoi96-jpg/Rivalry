from fastapi import APIRouter

from core.impact.models import BusinessImpact
from core.relevance.models import RelevanceProfile, RelevanceScore
from core.relevance.scorer import score_impact_relevance

router=APIRouter(prefix="/relevance",tags=["relevance"])

@router.post("/score",response_model=RelevanceScore)
def relevance_score(impact: BusinessImpact, profile: RelevanceProfile | None = None):
    return score_impact_relevance(impact, profile)
