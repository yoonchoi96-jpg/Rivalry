from core.business.depth import plan_question_depth
from core.business.models import BusinessProfile, QuestionDepth


def test_small_local_business_starts_shallow():
    plan = plan_question_depth(BusinessProfile(business_model="local_service", business_size="small"))
    assert plan.depth == QuestionDepth.LEVEL_1


def test_complex_small_business_can_require_deep_context():
    plan = plan_question_depth(BusinessProfile(
        business_model="importer", business_size="small", geographic_scope="international",
        product_count=120, customer_count=1500, supply_chain_complexity=90,
        channel_count=4, decision_complexity=80,
    ))
    assert plan.depth.value in {"level_5", "level_6", "level_7"}


def test_large_simple_business_is_not_automatically_deep():
    plan = plan_question_depth(BusinessProfile(
        business_model="simple_local_operation", business_size="large", geographic_scope="local",
        product_count=3, customer_count=100, supply_chain_complexity=5, channel_count=1,
        organization_complexity=5, decision_complexity=5,
    ))
    assert plan.depth.value in {"level_1", "level_2", "level_3"}


def test_unknown_context_stays_minimal():
    plan = plan_question_depth(BusinessProfile())
    assert plan.depth == QuestionDepth.LEVEL_1
    assert plan.next_topics == ["business identity"]
