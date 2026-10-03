from collections import Counter
from datetime import datetime, timezone
from uuid import uuid4

from .models import Change, Prediction


class PredictionEngine:
    """Heuristic prediction skeleton, not a machine-learning claim."""

    def predict(self, competitor_id: str, history: list[Change]) -> list[Prediction]:
        changes = [c for c in history if c.competitor_id == competitor_id]
        counts = Counter(c.type for c in changes)
        now = datetime.now(timezone.utc).isoformat()
        results = []
        for change_type, count in counts.items():
            if count < 2:
                continue
            matching = [c for c in changes if c.type == change_type]
            results.append(Prediction(
                id=str(uuid4()),
                competitor_id=competitor_id,
                prediction_type=f"repeat_{change_type.lower()}",
                predicted_at=now,
                expected_window_days=30,
                probability=min(90.0, 45.0 + count * 8.0),
                evidence_change_ids=[c.id for c in matching[-5:]],
            ))
        return results
