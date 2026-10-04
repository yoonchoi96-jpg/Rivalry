from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from time import perf_counter

from .evidence import AIProviderEvidence
from .gateway import OpenAIGateway
from .models import AIRequest, AIResponse, AIUseCase
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
        self.provider_performance: dict[str, tuple[float, float, int]] = {}

    def run(self, request: AIRequest, *, providers: list[str] | None = None) -> AIResponse:
        decision = self.router.select(request) if providers is None else None
        names = providers if providers is not None else self._adaptive_names(request, decision.providers)

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

        self._record_performance(results, {item.provider: score for item, score in zip(results, quality_scores)})
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

    def _adaptive_names(self, request: AIRequest, candidates: list[str]) -> list[str]:
        candidates = [name for name in dict.fromkeys(candidates) if self.provider_health.allow(name)]
        affinity = {"openai":100,"perplexity":98,"claude":96,"gemini":94,"deepseek":90,"naver":88,"qwen":88,"grok":86}
        scored = []
        for name in candidates:
            quality, latency, samples = self.provider_performance.get(name, (70.0, 1500.0, 0))
            latency_score = 100 if latency <= 500 else 90 if latency <= 1500 else 75 if latency <= 3000 else 50
            cost_score = self.router.COST_SCORE.get(name, 70.0)
            score = affinity.get(name,70)*0.40 + quality*0.25 + latency_score*0.15 + cost_score*0.10 + (95 if samples == 0 else 70)*0.10
            scored.append((score,name))
        scored.sort(reverse=True)
        return [name for _,name in scored[: {AIUseCase.CHAT:1, AIUseCase.INTELLIGENCE:3, AIUseCase.EXPERT:3}[request.use_case]]]

    def _record_performance(self, results: list[ProviderResult], qualities: dict[str,float]) -> None:
        for result in results:
            if not result.available:
                continue
            old_quality, old_latency, samples = self.provider_performance.get(result.provider,(70.0,1500.0,0))
            alpha = 1.0 if samples == 0 else 0.35
            quality = (1-alpha)*old_quality + alpha*qualities.get(result.provider,0.0)
            latency = old_latency if result.latency_ms is None else (1-alpha)*old_latency + alpha*result.latency_ms
            self.provider_performance[result.provider]=(round(quality,2),round(latency,2),samples+1)

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
