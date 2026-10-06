from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from core.business.models import QuestionDepth


class IntentKind(StrEnum):
    UNDERSTAND = "understand"
    MONITOR = "monitor"
    EXPLAIN = "explain"
    COMPARE = "compare"
    PREDICT = "predict"
    DECIDE = "decide"
    EXPERIMENT = "experiment"


class IntentPlan(BaseModel):
    kind: IntentKind
    question_depth: QuestionDepth
    known: list[str] = Field(default_factory=list)
    inferable: list[str] = Field(default_factory=list)
    research_candidates: list[str] = Field(default_factory=list)
    required_questions: list[str] = Field(default_factory=list)
    rationale: list[str] = Field(default_factory=list)
