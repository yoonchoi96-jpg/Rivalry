from __future__ import annotations

import os
from dataclasses import dataclass

from .models import AIRequest, AIUseCase


@dataclass(frozen=True)
class RoutingDecision:
    providers: list[str]
    reason: str


class AIRouter:
    """Selects the smallest useful provider set for a request.

    Provider selection is intentionally deterministic for the MVP. Later,
    health/cost/quality telemetry can replace the static policy without
    changing callers.
    """

    DEFAULTS = {
        AIUseCase.CHAT: ["openai"],
        AIUseCase.INTELLIGENCE: ["openai", "perplexity", "deepseek"],
        AIUseCase.EXPERT: ["openai", "claude", "gemini"],
    }

    def select(self, request: AIRequest) -> RoutingDecision:
        forced = self._forced_providers()
        if forced:
            return RoutingDecision(forced, "explicit provider override")

        text = request.message.lower()
        providers = list(self.DEFAULTS[request.use_case])
        reasons: list[str] = [request.use_case.value]

        if self._needs_latest_web(text):
            self._add(providers, "perplexity")
            reasons.append("latest/web")
        if self._needs_korean_context(text):
            self._add(providers, "naver")
            reasons.append("korean")
        if self._needs_china_context(text):
            self._add(providers, "qwen")
            reasons.append("china/chinese")
        if self._needs_social_signal(text):
            self._add(providers, "grok")
            reasons.append("social/trend")
        if self._needs_deep_analysis(text):
            self._add(providers, "claude")
            self._add(providers, "gemini")
            reasons.append("deep-analysis")

        return RoutingDecision(providers, ", ".join(reasons))

    @staticmethod
    def _forced_providers() -> list[str]:
        raw = os.getenv("RIVALRY_AI_PROVIDERS", "").strip()
        return [item.strip() for item in raw.split(",") if item.strip()]

    @staticmethod
    def _add(providers: list[str], name: str) -> None:
        if name not in providers:
            providers.append(name)

    @staticmethod
    def _needs_latest_web(text: str) -> bool:
        keywords = ("최신", "오늘", "최근", "뉴스", "시장", "가격", "트렌드", "latest", "today", "news", "market")
        return any(keyword in text for keyword in keywords)

    @staticmethod
    def _needs_korean_context(text: str) -> bool:
        keywords = ("네이버", "배민", "쿠팡", "한국", "국내", "서울", "한국어", "korea", "korean")
        return any(keyword in text for keyword in keywords)

    @staticmethod
    def _needs_china_context(text: str) -> bool:
        keywords = ("중국", "중국어", "중국 시장", "알리바바", "타오바오", "티몰", "china", "chinese", "alibaba", "taobao")
        return any(keyword in text for keyword in keywords)

    @staticmethod
    def _needs_social_signal(text: str) -> bool:
        keywords = ("sns", "소셜", "트위터", "x.com", "바이럴", "여론", "social", "viral")
        return any(keyword in text for keyword in keywords)

    @staticmethod
    def _needs_deep_analysis(text: str) -> bool:
        keywords = ("왜", "원인", "전략", "심층", "분석", "예측", "why", "cause", "strategy", "predict")
        return any(keyword in text for keyword in keywords)
