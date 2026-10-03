from fastapi import APIRouter
from engines.onboarding.models import OnboardingMessage, OnboardingState

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

@router.post("/state", response_model=OnboardingState)
def onboarding_state(messages: list[OnboardingMessage]):
    state = OnboardingState(messages=messages)
    text = " ".join(m.content.lower() for m in messages if m.role == "user")
    if any(k in text for k in ["배민", "쿠팡이츠", "스마트스토어", "shopify", "amazon", "rakuten"]):
        state.missing_inputs = [x for x in state.missing_inputs if x.value != "platform"]
    return state
