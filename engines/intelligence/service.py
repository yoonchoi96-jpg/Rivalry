from engines.change_detection.scoring import impact_score
from .models import CauseHypothesis, CauseType, IntelligenceReport

class IntelligenceService:
    def analyze_change(self, change, *, market_relevance=50, competitor_importance=50, persistence=50, evidence=None):
        evidence = evidence or []
        score = impact_score(change.magnitude, 50, market_relevance, competitor_importance, persistence)
        hypotheses = []
        if change.type == "PRICE_CHANGED":
            hypotheses = [
                CauseHypothesis(type=CauseType.COST, probability=60, evidence=evidence, confidence=55),
                CauseHypothesis(type=CauseType.COMPETITION, probability=50, evidence=evidence, confidence=50),
                CauseHypothesis(type=CauseType.POSITIONING, probability=40, evidence=evidence, confidence=45),
            ]
        return IntelligenceReport(change_id=change.id, summary=f"Material change detected: {change.type} (impact {score}).", hypotheses=hypotheses, confidence=min(95, score))
