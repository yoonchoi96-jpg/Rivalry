from __future__ import annotations

from dataclasses import dataclass, field

from .models import AIRequest, AIUseCase
from .provider_health import ProviderHealth


@dataclass(frozen=True)
class ProviderProfile:
    name: str
    suitability: dict[AIUseCase, float] = field(default_factory=dict)
    cost_score: float = 70.0
    default_latency_ms: float = 1500.0


@dataclass
class ProviderPerformance:
    quality: float = 70.0
    latency_ms: float = 1500.0
    samples: int = 0


@dataclass(frozen=True)
class ProviderScore:
    provider: str
    score: float
    suitability: float
    quality: float
    latency: float
    cost: float
    exploration: float


class AdaptiveAIRouter:
    """Adaptive provider ranking using task fit, quality, latency, cost and exploration."""

    LIMITS = {AIUseCase.CHAT: 1, AIUseCase.INTELLIGENCE: 3, AIUseCase.EXPERT: 3}

    def __init__(self, health: ProviderHealth, profiles: list[ProviderProfile] | None = None):
        self.health = health
        self.profiles = {p.name: p for p in (profiles or self.default_profiles())}
        self.performance: dict[str, ProviderPerformance] = {}

    @staticmethod
    def default_profiles() -> list[ProviderProfile]:
        def p(name, chat, intelligence, expert, cost, latency):
            return ProviderProfile(
                name=name,
                suitability={
                    AIUseCase.CHAT: chat,
                    AIUseCase.INTELLIGENCE: intelligence,
                    AIUseCase.EXPERT: expert,
                },
                cost_score=cost,
                default_latency_ms=latency,
            )
        return [
            p("openai", 100, 100, 100, 65, 1500),
            p("perplexity", 82, 100, 92, 70, 1800),
            p("claude", 86, 96, 100, 60, 1800),
            p("gemini", 88, 94, 96, 90, 1300),
            p("deepseek", 84, 90, 82, 100, 1200),
            p("naver", 80, 88, 82, 88, 1400),
            p("qwen", 82, 88, 86, 95, 1300),
            p("grok", 80, 84, 82, 80, 1600),
        ]

    def select(self, request: AIRequest, candidates: list[str]) -> list[str]:
        ranked = self.rank(request, candidates)
        return [item.provider for item in ranked[: self.LIMITS[request.use_case]]]

    def rank(self, request: AIRequest, candidates: list[str]) -> list[ProviderScore]:
        result = []
        for name in dict.fromkeys(candidates):
            if not self.health.allow(name):
                continue
            profile = self.profiles.get(name, ProviderProfile(name=name))
            perf = self.performance.get(name, ProviderPerformance(default_latency_ms=profile.default_latency_ms))
            latency = self._latency_score(perf.latency_ms)
            exploration = 95.0 if perf.samples == 0 else 70.0
            score = (
                profile.suitability.get(request.use_case, 70.0) * 0.35
                + perf.quality * 0.25
                + latency * 0.15
                + profile.cost_score * 0.15
                + exploration * 0.10
            )
            result.append(ProviderScore(name, round(score, 2), profile.suitability.get(request.use_case, 70.0), perf.quality, latency, profile.cost_score, exploration))
        return sorted(result, key=lambda x: (x.score, x.provider), reverse=True)

    def record(self, provider: str, quality: float, latency_ms: float | None) -> None:
        perf = self.performance.setdefault(provider, ProviderPerformance())
        alpha = 1.0 if perf.samples == 0 else 0.35
        perf.quality = round((1 - alpha) * perf.quality + alpha * quality, 2)
        if latency_ms is not None:
            perf.latency_ms = round((1 - alpha) * perf.latency_ms + alpha * latency_ms, 2)
        perf.samples += 1
