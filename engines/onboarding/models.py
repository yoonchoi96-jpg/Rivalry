from enum import StrEnum
from pydantic import BaseModel

class InputKind(StrEnum):
    BUSINESS = "business"
    PLATFORM = "platform"
    COMPETITOR = "competitor"
    DOCUMENT = "document"
    WEBSITE = "website"
    GOAL = "goal"

class OnboardingMessage(BaseModel):
    role: str
    content: str

class OnboardingState(BaseModel):
    business_id: str | None = None
    completed: bool = False
    messages: list[OnboardingMessage] = []
    missing_inputs: list[InputKind] = [InputKind.BUSINESS, InputKind.PLATFORM, InputKind.GOAL]
