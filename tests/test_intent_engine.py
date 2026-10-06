from core.business.models import BusinessProfile, QuestionDepth
from core.intent.engine import build_intent_plan, classify_intent
from core.intent.models import IntentKind


def test_classify_intent_prefers_explicit_explanation():
    assert classify_intent("왜 매출이 떨어졌는지 원인을 알려줘") == IntentKind.EXPLAIN


def test_intent_plan_researches_before_asking():
    plan = build_intent_plan("우리 가격을 비교해줘", BusinessProfile())
    assert plan.kind == IntentKind.COMPARE
    assert "relevant external signals" in plan.research_candidates
    assert plan.required_questions == []
    assert plan.question_depth == QuestionDepth.LEVEL_1


def test_intent_plan_only_asks_for_missing_context():
    plan = build_intent_plan("", None)
    assert "business identity" in plan.required_questions
    assert "current goal" in plan.required_questions
