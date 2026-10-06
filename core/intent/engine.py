from __future__ import annotations

from core.business.depth import plan_question_depth
from core.business.models import BusinessProfile, QuestionDepth
from core.intent.models import IntentKind, IntentPlan


_KEYWORDS: dict[IntentKind, tuple[str, ...]] = {
    IntentKind.EXPLAIN: ("왜", "원인", "이유", "why", "cause"),
    IntentKind.COMPARE: ("비교", "대비", "compare", "vs", "차이"),
    IntentKind.PREDICT: ("예측", "전망", "앞으로", "forecast", "predict"),
    IntentKind.DECIDE: ("결정", "어떻게 할까", "사야", "팔아", "가격을", "decide"),
    IntentKind.MONITOR: ("추적", "모니터", "변화", "알려줘", "monitor", "change"),
    IntentKind.EXPERIMENT: ("실험", "테스트", "시험", "experiment"),
}


def classify_intent(text: str) -> IntentKind:
    normalized = text.lower()
    for kind, keywords in _KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return kind
    return IntentKind.UNDERSTAND


def build_intent_plan(
    text: str,
    profile: BusinessProfile | None = None,
    *,
    known: list[str] | None = None,
) -> IntentPlan:
    known_items = list(known or [])
    questions: list[str] = []
    if profile is None:
        questions.append("business identity")
    if not text.strip():
        questions.append("current goal")

    depth = plan_question_depth(profile or BusinessProfile()).depth if profile else QuestionDepth.LEVEL_1
    return IntentPlan(
        kind=classify_intent(text),
        question_depth=depth,
        known=known_items,
        inferable=["business context", "publicly observable market context"],
        research_candidates=["relevant external signals", "evidence supporting the answer"],
        required_questions=questions,
        rationale=[
            "infer available context before asking the user",
            "research public evidence before requesting information the system can obtain",
        ],
    )
