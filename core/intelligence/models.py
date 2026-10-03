from __future__ import annotations

from enum import StrEnum
from pydantic import BaseModel, Field


class Sentiment(StrEnum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class CostSignalType(StrEnum):
    INGREDIENT = "ingredient"
    LABOR = "labor"
    RENT = "rent"
    LOGISTICS = "logistics"
    SUPPLIER = "supplier"
    FX = "fx"
    OTHER = "other"


class Change(BaseModel):
    id: str
    competitor_id: str
    type: str
    before: object | None = None
    after: object | None = None
    magnitude: float = 0
    severity: str = "info"
    impact_score: float = Field(0, ge=0, le=100)
    confidence: float = Field(0, ge=0, le=100)
    detected_at: str
    source: str = ""


class Review(BaseModel):
    id: str
    competitor_id: str
    rating: float | None = Field(default=None, ge=0, le=5)
    text: str = ""
    created_at: str
    sentiment: Sentiment | None = None
    topics: list[str] = Field(default_factory=list)
    product_id: str | None = None
    source: str = ""
    confidence: float = Field(default=0, ge=0, le=100)


class CostSignal(BaseModel):
    id: str
    product_id: str | None = None
    type: CostSignalType
    name: str
    before: float | None = None
    after: float | None = None
    unit: str = ""
    observed_at: str
    source: str = ""
    confidence: float = Field(default=0, ge=0, le=100)


class MarginEstimate(BaseModel):
    product_id: str
    price_low: float
    price_high: float
    cost_low: float
    cost_high: float
    gross_margin_low_pct: float = Field(ge=0, le=100)
    gross_margin_high_pct: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=100)
    methodology: str


class Prediction(BaseModel):
    id: str
    competitor_id: str
    prediction_type: str
    predicted_at: str
    expected_window_days: int = Field(ge=0)
    probability: float = Field(ge=0, le=100)
    evidence_change_ids: list[str] = Field(default_factory=list)
    outcome: str | None = None
    outcome_at: str | None = None
