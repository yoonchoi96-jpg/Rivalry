from pydantic import BaseModel, Field

from .models import Change


class IntelligenceAlert(BaseModel):
    change_id: str
    competitor_id: str
    change_type: str
    summary: str
    impact_score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=100)
    likely_cause: str
    recommended_action: str
    evidence_ids: list[str] = []


class AlertIntelligenceEngine:
    """Deterministic alert layer; AI enrichment can be added later."""

    def build(self, changes: list[Change]) -> list[IntelligenceAlert]:
        ordered = sorted(changes, key=lambda c: (c.impact_score, c.confidence), reverse=True)
        return [self._one(c) for c in ordered]

    def _one(self, change: Change) -> IntelligenceAlert:
        return IntelligenceAlert(
            change_id=change.id,
            competitor_id=change.competitor_id,
            change_type=change.type,
            summary=f"{change.type} 변화가 감지되었습니다.",
            impact_score=change.impact_score,
            confidence=change.confidence,
            likely_cause="경쟁사의 전략 또는 운영 변화 가능성",
            recommended_action=(
                "가격·상품·프로모션 대응안을 비교하세요."
                if change.impact_score >= 70
                else "관련 지표를 추가 확인한 뒤 대응 필요성을 판단하세요."
            ),
            evidence_ids=[change.id],
        )
