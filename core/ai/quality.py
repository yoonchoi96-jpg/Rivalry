from __future__ import annotations

from .providers import ProviderResult


class AIQualityScorer:
    """Operational heuristic for provider-result usefulness."""

    def score(self, result: ProviderResult, observed_intelligence: object = None) -> tuple[float, list[str]]:
        if not result.available or not result.text.strip():
            return 0.0, ["unavailable_or_empty"]

        completeness = min(95.0, 45.0 + len(result.text.strip()) / 6.0)
        if result.latency_ms is None:
            latency = 70.0
        elif result.latency_ms <= 500:
            latency = 100.0
        elif result.latency_ms <= 1500:
            latency = 90.0
        elif result.latency_ms <= 3000:
            latency = 75.0
        else:
            latency = 50.0

        alignment = 70.0
        if observed_intelligence:
            tokens = [t.lower() for t in str(observed_intelligence).split() if len(t) >= 4]
            hits = sum(1 for token in set(tokens) if token in result.text.lower())
            alignment = min(100.0, 60.0 + hits * 10.0)

        score = round(25.0 + completeness * 0.35 + latency * 0.15 + alignment * 0.25, 2)
        return score, [
            f"completeness={completeness:.0f}",
            f"latency={latency:.0f}",
            f"rivalry_alignment={alignment:.0f}",
        ]
