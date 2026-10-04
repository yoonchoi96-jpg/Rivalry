from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from .evidence import AIProviderEvidence
from .gateway import OpenAIGateway
from .models import AIRequest, AIResponse
from .providers import ProviderRegistry, ProviderResult
from .router import AIRouter


class MultiAIOrchestrator:
    """Routes a request to selected AI providers and synthesizes their evidence."""

    def __init__(
        self,
        registry: ProviderRegistry | None = None,
        synthesizer: OpenAIGateway | None = None,
        router: AIRouter | None = None,
        max_workers: int = 4,
    ):
        self.registry = registry or ProviderRegistry()
        self.synthesizer = synthesizer or OpenAIGateway()
        self.router = router or AIRouter()
        self.max_workers = max_workers

    def run(self, request: AIRequest, *, providers: list[str] | None = None) -> AIResponse:
        decision = self.router.select(request) if providers is None else None
        names = providers if providers is not None else decision.providers

        if not names:
            return AIResponse(text="선택된 AI provider가 없습니다.", model="multi-ai", usage={})

        research_context = request.context.get("rivalry_intelligence", {})
        prompt = self._research_prompt(
            request,
            decision.reason if decision else "explicit",
            research_context,
        )
        results = self._fan_out(names, prompt)
        evidence = "\n\n".join(
            f"[{item.provider} / {item.model}]\n{item.text}"
            for item in results if item.available and item.text
        )
        if not evidence:
            return AIResponse(text="사용 가능한 AI provider가 없습니다.", model="multi-ai", usage={})

        synthesis_prompt = (
            "Synthesize the independent AI findings below for Rivalry. "
            "Resolve contradictions, separate facts from hypotheses, and state uncertainty. "
            "Prefer Rivalry-observed data over generic model claims.\n\n"
            f"USER REQUEST:\n{request.message}\n\n"
            f"ROUTING:\n{decision.reason if decision else 'explicit'}\n\n"
            f"FINDINGS:\n{evidence}"
        )
        final = self.synthesizer.respond(request.model_copy(update={"message": synthesis_prompt}))
        evidence_items = [
            AIProviderEvidence(
                provider=item.provider,
                model=item.model,
                available=item.available,
                text=item.text,
                error=item.error,
            ).model_dump()
            for item in results
        ]
        available_count = sum(1 for item in results if item.available and item.text)
        confidence = min(100.0, 40.0 + available_count * 20.0) if results else 0.0
        return final.model_copy(update={
            "model": f"multi-ai->{final.model}",
            "confidence": confidence,
            "evidence": evidence_items,
        })

    def _fan_out(self, names: list[str], prompt: str) -> list[ProviderResult]:
        def call(name: str) -> ProviderResult:
            try:
                provider = self.registry.by_name(name)
                return provider.generate(prompt, system=self._system())
            except Exception as exc:
                return ProviderResult(
                    provider=name, model="", text="", available=False, error=exc.__class__.__name__
                )

        worker_count = max(1, min(self.max_workers, len(names)))
        with ThreadPoolExecutor(max_workers=worker_count) as pool:
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
    def _research_prompt(
        request: AIRequest,
        routing_reason: str,
        intelligence: object,
    ) -> str:
        return (
            f"Business ID: {request.business_id or 'unknown'}\n"
            f"Context: {request.context}\n"
            f"Routing reason: {routing_reason}\n"
            f"Rivalry observed intelligence: {intelligence}\n"
            f"User request: {request.message}\n"
            "Treat Rivalry observed intelligence as primary first-party evidence. "
            "Clearly distinguish observed facts from external research and hypotheses. "
            "Investigate this request independently and provide concise findings "
            "that another model can cross-check."
        )
