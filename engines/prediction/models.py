from pydantic import BaseModel, Field

class Prediction(BaseModel):
    id: str
    competitor_id: str
    prediction_type: str
    predicted_at: str
    expected_window_days: int = Field(ge=0)
    probability: float = Field(ge=0, le=100)
    evidence_change_ids: list[str] = []
    outcome: str | None = None
    outcome_at: str | None = None
