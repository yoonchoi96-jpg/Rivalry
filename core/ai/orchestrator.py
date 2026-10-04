from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from time import perf_counter

from .evidence import AIProviderEvidence
from .gateway import OpenAIGateway
from .models import AIRequest, AIResponse
from .providers import ProviderRegistry, ProviderResult
from .quality import AIQualityScorer
from .provider_health import ProviderHealth
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
        self.quality_scorer = AIQualityScorer()
        self.provider_health = ProviderHealth()
        self.max_retries = 2

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
        evidence_items = []
        quality_scores = []
        for item in results:
            quality_score, quality_reasons = self.quality_scorer.score(
                item,
                observed_intelligence=research_context,
            )
            quality_scores.append(quality_score)
            evidence_items.append(
                AIProviderEvidence(
                    provider=item.provider,
                    model=item.model,
                    available=item.available,
                    text=item.text,
                    latency_ms=item.latency_ms,
                    usage=item.usage or {},
                    error=item.error,
                    quality_score=quality_score,
                    quality_reasons=quality_reasons,
                ).model_dump()
            )

        confidence = round(sum(quality_scores) / len(quality_scores), 2) if quality_scores else 0.0
        return final.model_copy(update={
            "model": f"multi-ai->{final.model}",
            "confidence": confidence,
            "evidence": evidence_items,
        })

    def _fan_out(self, names: list[str], prompt: str) -> list[ProviderResult]:
        def call(name: str) -> ProviderResult:
            if not self.provider_health.allow(name):
                return ProviderResult(
                    provider=name,
                    model="",
                    text="",
                    available=False,
                    error="provider_temporarily_blocked",
                    latency_ms=0,
                    usage={},
                )

            started = perf_counter()
            last_error = "provider_failed"
            for attempt in range(self.max_retries + 1):
                try:
                    provider = self.registry.by_name(name)
                    result = provider.generate(prompt, system=self._system())
                    self.provider_health.success(name)
                    return ProviderResult(
                        provider=result.provider,
                        model=result.model,
                        text=result.text,
                        available=result.available,
                        error=result.error,
                        latency_ms=int((perf_counter() - started) * 1000),
                        usage=result.usage or {},
                    )
                except Exception as exc:
                    last_error = exc.__class__.__name__
                    if attempt < self.max_retries:
                        continue
                    self.provider_health.failure(name, last_error)

            return ProviderResult(
                provider=name,
                model="",
                text="",
                available=False,
                error=last_error,
                latency_ms=int((perf_counter() - started) * 1000),
                usage={},
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
