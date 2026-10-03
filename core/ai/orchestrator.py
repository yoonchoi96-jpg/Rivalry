from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from .gateway import OpenAIGateway
from .models import AIRequest, AIResponse
from .providers import ProviderRegistry, ProviderResult


class MultiAIOrchestrator:
    """Uses multiple independent AI APIs, then lets a designated synthesizer judge them.

    This is deliberately separate from the normal single-provider tool runtime:
    external research/second opinions can fan out in parallel, while final
    product behavior remains deterministic and provider-swappable.
    """

    def __init__(
        self,
        registry: ProviderRegistry | None = None,
        synthesizer: OpenAIGateway | None = None,
        max_workers: int = 3,
    ):
        self.registry = registry or ProviderRegistry()
        self.synthesizer = synthesizer or OpenAIGateway()
        self.max_workers = max_workers

    def run(
        self,
        request: AIRequest,
        *,
        providers: list[str] | None = None,
    ) -> AIResponse:
        names = providers or self.registry.available_names()
        prompt = self._research_prompt(request)
        results = self._fan_out(names, prompt)

        evidence = "\n\n".join(
            f"[{item.provider} / {item.model}]\n{item.text}"
            for item in results
            if item.available and item.text
        )
        if not evidence:
            return AIResponse(
                text="사용 가능한 AI provider가 없습니다.",
                model="multi-ai",
                usage={},
            )

        synthesis_prompt = (
            "Synthesize the independent AI findings below for Rivalry. "
            "Do not blindly trust any provider. Resolve contradictions, "
            "separate facts from hypotheses, and state uncertainty.\n\n"
            f"USER REQUEST:\n{request.message}\n\n"
            f"FINDINGS:\n{evidence}"
        )
        final = self.synthesizer.respond(
            request.model_copy(update={"message": synthesis_prompt})
        )
        return final.model_copy(
            update={
                "model": f"multi-ai->{final.model}",
                "context": None,
            }
        )

    def _fan_out(self, names: list[str], prompt: str) -> list[ProviderResult]:
        def call(name: str) -> ProviderResult:
            provider = self.registry.by_name(name)
            try:
                return provider.generate(prompt, system=self._system())
            except Exception as exc:
                return ProviderResult(
                    provider=name,
                    model=getattr(provider, "model", ""),
                    text="",
                    available=False,
                    error=exc.__class__.__name__,
                )

        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(names))) as pool:
            futures = [pool.submit(call, name) for name in names]
            return [future.result() for future in as_completed(futures)]

    @staticmethod
    def _system() -> str:
        return (
            "You are one research component inside Rivalry. "
            "Return evidence, reasoning, and uncertainty. Never invent facts. "
            "If web/current information is needed, use your provider's supported "
            "retrieval capability rather than pretending you know it."
        )

    @staticmethod
    def _research_prompt(request: AIRequest) -> str:
        return (
            f"Business ID: {request.business_id or 'unknown'}\n"
            f"Context: {request.context}\n"
            f"User request: {request.message}\n"
            "Investigate this request independently and provide concise findings "
            "that another model can cross-check."
        )
