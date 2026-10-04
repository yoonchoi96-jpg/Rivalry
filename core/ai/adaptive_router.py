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
    capabilities: dict[str, float] = field(default_factory=dict)


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
    capability: float


class AdaptiveAIRouter:
    """Adaptive provider ranking using task fit, quality, latency, cost and exploration."""

    LIMITS = {AIUseCase.CHAT: 1, AIUseCase.INTELLIGENCE: 3, AIUseCase.EXPERT: 3}

    def __init__(self, health: ProviderHealth, profiles: list[ProviderProfile] | None = None):
        self.health = health
        self.profiles = {p.name: p for p in (profiles or self.default_profiles())}
        self.performance: dict[str, ProviderPerformance] = {}

    @staticmethod
    def default_profiles() -> list[ProviderProfile]:
        def p(name, chat, intelligence, expert, cost, latency, capabilities=None):
            return ProviderProfile(
                name=name,
                suitability={
                    AIUseCase.CHAT: chat,
                    AIUseCase.INTELLIGENCE: intelligence,
                    AIUseCase.EXPERT: expert,
                },
                cost_score=cost,
                default_latency_ms=latency,
                capabilities=capabilities or {},
            )
        return [
            p("openai", 100, 100, 100, 65, 1500, {"general": 95}),
            p("perplexity", 82, 100, 92, 70, 1800, {"latest_web": 100, "market": 95}),
            p("claude", 86, 96, 100, 60, 1800, {"deep_analysis": 100, "strategy": 100}),
            p("gemini", 88, 94, 96, 90, 1300, {"deep_analysis": 95, "general": 90}),
            p("deepseek", 84, 90, 82, 100, 1200, {"bulk": 100, "general": 88}),
            p("naver", 80, 88, 82, 88, 1400, {"korean": 100, "korean_market": 100}),
            p("qwen", 82, 88, 86, 95, 1300, {"china": 100, "chinese": 100}),
            p("grok", 80, 84, 82, 80, 1600, {"social": 100, "trend": 100}),
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
            perf = self.performance.get(name, ProviderPerformance(latency_ms=profile.default_latency_ms))
            latency = self._latency_score(perf.latency_ms)
            capability = self._capability_score(request.message.lower(), profile.capabilities)
            exploration = 95.0 if perf.samples == 0 else 70.0
            score = (
                profile.suitability.get(request.use_case, 70.0) * 0.25
                + capability * 0.25
                + perf.quality * 0.25
                + latency * 0.10
                + profile.cost_score * 0.10
                + exploration * 0.05
            )
            result.append(ProviderScore(name, round(score, 2), profile.suitability.get(request.use_case, 70.0), perf.quality, latency, profile.cost_score, exploration, capability))
        return sorted(result, key=lambda x: (x.score, x.provider), reverse=True)


    @staticmethod
    def _latency_score(latency_ms: float) -> float:
        if latency_ms <= 500: return 100.0
        if latency_ms <= 1500: return 90.0
        if latency_ms <= 3000: return 75.0
        return 50.0

    @staticmethod
    def _capability_score(text: str, capabilities: dict[str, float]) -> float:
        signals = {
            "latest_web": ("최신", "오늘", "최근", "뉴스", "latest", "today", "news"),
            "market": ("시장", "가격", "경쟁사", "market", "price", "competitor"),
            "korean": ("한국", "국내", "네이버", "배민", "쿠팡", "korean", "korea"),
            "korean_market": ("한국 시장", "국내 시장", "한국 소비자"),
            "china": ("중국", "알리바바", "타오바오", "티몰", "china", "alibaba", "taobao"),
            "chinese": ("중국어", "중문", "chinese"),
            "social": ("sns", "소셜", "트위터", "x.com", "여론", "viral", "social"),
            "trend": ("트렌드", "유행", "바이럴", "trend"),
            "deep_analysis": ("분석", "심층", "원인", "왜", "analysis", "cause", "why"),
            "strategy": ("전략", "예측", "strategy", "predict"),
            "bulk": ("대량", "bulk", "일괄"),
            "general": ("질문", "설명", "question", "explain"),
        }
        matches = [capabilities[key] for key, words in signals.items() if key in capabilities and any(w in text for w in words)]
        return max(matches, default=70.0)

    def record(self, provider: str, quality: float, latency_ms: float | None) -> None:
        perf = self.performance.setdefault(provider, ProviderPerformance())
        alpha = 1.0 if perf.samples == 0 else 0.35
        perf.quality = round((1 - alpha) * perf.quality + alpha * quality, 2)
        if latency_ms is not None:
            perf.latency_ms = round((1 - alpha) * perf.latency_ms + alpha * latency_ms, 2)
        perf.samples += 1
