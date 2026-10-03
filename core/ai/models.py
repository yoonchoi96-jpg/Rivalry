from enum import StrEnum
from pydantic import BaseModel, Field


class AIUseCase(StrEnum):
    CHAT = "chat"
    INTELLIGENCE = "intelligence"
    EXPERT = "expert"


class AIRequest(BaseModel):
    message: str = Field(min_length=1)
    use_case: AIUseCase = AIUseCase.CHAT
    conversation_id: str | None = None
    business_id: str | None = None
    context: dict[str, object] = Field(default_factory=dict)


class AIResponse(BaseModel):
    text: str
    model: str
    response_id: str | None = None
    usage: dict[str, int] = Field(default_factory=dict)
