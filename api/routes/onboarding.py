from fastapi import APIRouter

from core.business.depth import plan_question_depth
from core.business.models import BusinessProfile
from engines.onboarding.models import OnboardingMessage, OnboardingState

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.post("/state", response_model=OnboardingState)
def onboarding_state(
    messages: list[OnboardingMessage],
    business_profile: BusinessProfile | None = None,
):
    state = OnboardingState(messages=messages, business_profile=business_profile)
    text = " ".join(m.content.lower() for m in messages if m.role == "user")
    if any(k in text for k in ["배민", "쿠팡이츠", "스마트스토어", "shopify", "amazon", "rakuten"]):
        state.missing_inputs = [x for x in state.missing_inputs if x.value != "platform"]

    plan = plan_question_depth(business_profile or BusinessProfile())
    state.question_depth = plan.depth
    state.next_topics = plan.next_topics
    return state
