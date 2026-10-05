from enum import StrEnum

from pydantic import BaseModel, Field

from core.business.models import BusinessProfile, QuestionDepth


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
    messages: list[OnboardingMessage] = Field(default_factory=list)
    missing_inputs: list[InputKind] = Field(default_factory=lambda: [
        InputKind.BUSINESS, InputKind.PLATFORM, InputKind.GOAL
    ])
    business_profile: BusinessProfile | None = None
    question_depth: QuestionDepth = QuestionDepth.LEVEL_1
    next_topics: list[str] = Field(default_factory=lambda: ["business identity"])
