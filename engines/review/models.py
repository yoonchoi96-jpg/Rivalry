from enum import StrEnum
from pydantic import BaseModel, Field

class Sentiment(StrEnum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"

class Review(BaseModel):
    id: str
    competitor_id: str
    rating: float | None = Field(default=None, ge=0, le=5)
    text: str = ""
    created_at: str
    sentiment: Sentiment | None = None
    topics: list[str] = []
    product_id: str | None = None
    source: str = ""
    confidence: float = Field(default=0, ge=0, le=100)
