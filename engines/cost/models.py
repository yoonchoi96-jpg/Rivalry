from enum import StrEnum
from pydantic import BaseModel, Field

class CostSignalType(StrEnum):
    INGREDIENT = "ingredient"
    LABOR = "labor"
    RENT = "rent"
    LOGISTICS = "logistics"
    SUPPLIER = "supplier"
    FX = "fx"
    OTHER = "other"

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
