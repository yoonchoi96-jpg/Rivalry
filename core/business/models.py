from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class QuestionDepth(StrEnum):
    LEVEL_1 = "level_1"
    LEVEL_2 = "level_2"
    LEVEL_3 = "level_3"
    LEVEL_4 = "level_4"
    LEVEL_5 = "level_5"
    LEVEL_6 = "level_6"
    LEVEL_7 = "level_7"


class BusinessProfile(BaseModel):
    """Normalized business context used to decide what Rivalry needs to ask next.

    Complexity is multi-dimensional. Size is one input, never the deciding rule.
    """

    business_model: str | None = None
    business_size: str | None = None
    complexity: int = Field(default=0, ge=0, le=100)
    geographic_scope: str | None = None
    product_count: int | None = Field(default=None, ge=0)
    customer_count: int | None = Field(default=None, ge=0)
    supply_chain_complexity: int = Field(default=0, ge=0, le=100)
    channel_count: int = Field(default=0, ge=0)
    organization_complexity: int = Field(default=0, ge=0, le=100)
    decision_complexity: int = Field(default=0, ge=0, le=100)
    user_role: str | None = None
    current_goal: str | None = None


class QuestionPlan(BaseModel):
    """The next onboarding depth and why it is required."""

    depth: QuestionDepth
    score: int = Field(ge=0, le=100)
    rationale: list[str] = Field(default_factory=list)
    next_topics: list[str] = Field(default_factory=list)
