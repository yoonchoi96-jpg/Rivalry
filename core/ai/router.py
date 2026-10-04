from __future__ import annotations

import os
from dataclasses import dataclass

from .models import AIRequest, AIUseCase


@dataclass(frozen=True)
class RoutingDecision:
    providers: list[str]
    reason: str


class AIRouter:
    """Selects the smallest useful provider set for a request."""

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
        reasons = [request.use_case.value]
        if self._needs_latest_web(text):
            self._add(providers, "perplexity"); reasons.append("latest/web")
        if self._needs_korean_context(text):
            self._add(providers, "naver"); reasons.append("korean")
        if self._needs_china_context(text):
            self._add(providers, "qwen"); reasons.append("china/chinese")
        if self._needs_social_signal(text):
            self._add(providers, "grok"); reasons.append("social/trend")
        if self._needs_deep_analysis(text):
            self._add(providers, "claude"); self._add(providers, "gemini"); reasons.append("deep-analysis")
        return RoutingDecision(providers, ", ".join(reasons))

    @staticmethod
    def _forced_providers() -> list[str]:
        raw = os.getenv("RIVALRY_AI_PROVIDERS", "").strip()
        return [item.strip() for item in raw.split(",") if item.strip()]

    @staticmethod
    def _add(providers, name):
        if name not in providers: providers.append(name)

    @staticmethod
    def _needs_latest_web(text):
        return any(k in text for k in ("최신","오늘","최근","뉴스","시장","가격","트렌드","latest","today","news","market"))
    @staticmethod
    def _needs_korean_context(text):
        return any(k in text for k in ("네이버","배민","쿠팡","한국","국내","서울","한국어","korea","korean"))
    @staticmethod
    def _needs_china_context(text):
        return any(k in text for k in ("중국","중국어","중국 시장","알리바바","타오바오","티몰","china","chinese","alibaba","taobao"))
    @staticmethod
    def _needs_social_signal(text):
        return any(k in text for k in ("sns","소셜","트위터","x.com","바이럴","여론","social","viral"))
    @staticmethod
    def _needs_deep_analysis(text):
        return any(k in text for k in ("왜","원인","전략","심층","분석","예측","why","cause","strategy","predict"))


    def limit_candidates(self, names: list[str], use_case: AIUseCase, health=None) -> list[str]:
        """Keep fan-out bounded and skip temporarily unavailable names."""
        names = list(dict.fromkeys(names))
        if health is not None:
            names = [name for name in names if health.allow(name)]
        limit = {AIUseCase.CHAT: 1, AIUseCase.INTELLIGENCE: 3, AIUseCase.EXPERT: 3}[use_case]
        return names[:limit]
