from __future__ import annotations

from core.business.entity import BusinessEntity
from core.business.models import BusinessProfile
from core.causal.models import CausalFactor, CausalMap, CausalRelation
from core.intent.models import IntentKind

_BASE_FACTORS = (
    ("demand", "고객 수요", CausalRelation.DIRECT, "매출·주문 변화는 수요 변화와 직접 연결될 수 있습니다."),
    ("competitive_price", "경쟁 가격", CausalRelation.DIRECT, "경쟁사의 가격 변화는 고객의 선택과 가격 경쟁에 직접 영향을 줄 수 있습니다."),
    ("promotion", "프로모션", CausalRelation.DIRECT, "할인·쿠폰·행사 변화는 단기 수요와 경쟁 행동에 영향을 줄 수 있습니다."),
    ("reviews", "고객 반응", CausalRelation.DIRECT, "리뷰·평점 변화는 구매 전환과 재방문에 영향을 줄 수 있습니다."),
    ("input_cost", "투입 비용", CausalRelation.UPSTREAM, "원재료·상품·부품 비용 변화는 마진 압력의 상류 원인이 될 수 있습니다."),
    ("labor", "인건비", CausalRelation.UPSTREAM, "임금과 인력 변화는 비용 구조와 운영 여력에 영향을 줄 수 있습니다."),
    ("rent_energy", "임대·에너지 비용", CausalRelation.UPSTREAM, "고정비와 에너지 비용 변화는 수익성에 영향을 줄 수 있습니다."),
    ("fx_logistics", "환율·물류", CausalRelation.UPSTREAM, "수입·수출 사업에서는 환율과 물류비가 원가와 가격에 전달될 수 있습니다."),
    ("market_conditions", "시장 환경", CausalRelation.UPSTREAM, "시장 성장률과 거시 환경은 수요·가격·비용에 간접적으로 영향을 줄 수 있습니다."),
    ("customer_outcome", "매출·마진 결과", CausalRelation.DOWNSTREAM, "최종 사업 결과를 관찰하면 원인 가설의 영향을 검증할 수 있습니다."),
)

def build_causal_map(question: str, business: BusinessEntity, *, intent: IntentKind = IntentKind.UNDERSTAND) -> CausalMap:
    profile = BusinessProfile.model_validate(business.profile) if business.profile else BusinessProfile()
    factors: list[CausalFactor] = []
    for key, label, relation, rationale in _BASE_FACTORS:
        priority = 50
        if intent in {IntentKind.EXPLAIN, IntentKind.DECIDE, IntentKind.PREDICT}:
            priority += 10
        if relation == CausalRelation.UPSTREAM and profile.supply_chain_complexity >= 40:
            priority += 15
        if relation == CausalRelation.DIRECT and profile.channel_count >= 2:
            priority += 10
        if key == "fx_logistics" and (profile.geographic_scope or "").lower() in {"international", "global"}:
            priority += 20
        factors.append(CausalFactor(key=key, label=label, relation=relation, rationale=rationale, priority=min(priority, 100)))
    factors.sort(key=lambda item: item.priority, reverse=True)
    return CausalMap(question=question, factors=factors)
