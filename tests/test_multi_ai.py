from types import SimpleNamespace

from core.ai.models import AIRequest
from core.ai.orchestrator import MultiAIOrchestrator
from core.ai.providers import AIProvider, ProviderRegistry, ProviderResult


class FakeProvider(AIProvider):
    def __init__(self, name: str, text: str):
        self.name = name
        self.model = f"{name}-test"
        self.text = text

    def generate(self, prompt: str, *, system: str = "") -> ProviderResult:
        return ProviderResult(self.name, self.model, self.text)


class FakeSynthesizer:
    def respond(self, request):
        return SimpleNamespace(
            text="통합 판단",
            model="gpt-test",
            response_id="final",
            usage={},
            confidence=0,
            evidence=[],
            model_copy=lambda update: SimpleNamespace(
                text="통합 판단",
                model=update["model"],
                response_id="final",
                usage={},
                confidence=update.get("confidence", 0),
                evidence=update.get("evidence", []),
            ),
        )


def test_multi_ai_fans_out_and_synthesizes():
    registry = ProviderRegistry([
        FakeProvider("openai", "가격 상승은 전략적일 수 있음"),
        FakeProvider("gemini", "상품 구성 변화가 관찰됨"),
        FakeProvider("perplexity", "최근 시장 비용 상승 신호가 있음"),
    ])
    orchestrator = MultiAIOrchestrator(
        registry=registry,
        synthesizer=FakeSynthesizer(),
    )

    result = orchestrator.run(
        AIRequest(message="경쟁사 가격 상승 이유를 분석해줘"),
        providers=["openai", "gemini", "perplexity"],
    )

    assert result.text == "통합 판단"
    assert result.model == "multi-ai->gpt-test"
    assert 0 <= result.confidence <= 100
    assert {item["provider"] for item in result.evidence} == {"openai", "gemini", "perplexity"}


def test_multi_ai_research_prompt_preserves_observed_intelligence():
    request = AIRequest(
        message="가격 변화 원인을 분석해줘",
        business_id="biz-1",
        context={"rivalry_intelligence": {"market_pulse": {"change_count": 2}}},
    )
    prompt = MultiAIOrchestrator._research_prompt(
        request,
        "explicit",
        request.context["rivalry_intelligence"],
    )
    assert "Rivalry observed intelligence" in prompt
    assert "change_count" in prompt


def test_provider_evidence_contains_telemetry():
    class TelemetryProvider(FakeProvider):
        def generate(self, prompt: str, *, system: str = "") -> ProviderResult:
            return ProviderResult(
                self.name,
                self.model,
                self.text,
                latency_ms=12,
                usage={"input_tokens": 10, "output_tokens": 5},
            )

    registry = ProviderRegistry([TelemetryProvider("openai", "openai-test")])
    result = MultiAIOrchestrator(
        registry=registry,
        synthesizer=FakeSynthesizer(),
    ).run(AIRequest(message="테스트"), providers=["openai"])

    evidence = result.evidence[0]
    assert evidence["latency_ms"] == 12
    assert evidence["usage"]["input_tokens"] == 10


def test_provider_quality_score_is_exposed_in_evidence():
    registry = ProviderRegistry([FakeProvider("openai", "충분히 긴 분석 결과입니다. 경쟁사 가격과 시장 변화의 관계를 설명합니다.")])
    result = MultiAIOrchestrator(
        registry=registry,
        synthesizer=FakeSynthesizer(),
    ).run(AIRequest(message="테스트"), providers=["openai"])

    evidence = result.evidence[0]
    assert 0 <= evidence["quality_score"] <= 100
    assert evidence["quality_reasons"]
    assert result.confidence == evidence["quality_score"]


def test_unavailable_provider_quality_is_zero():
    class BrokenProvider(FakeProvider):
        def generate(self, prompt: str, *, system: str = "") -> ProviderResult:
            return ProviderResult(self.name, self.model, "", available=False, error="down")

    result = MultiAIOrchestrator(
        registry=ProviderRegistry([BrokenProvider("openai", "")]),
        synthesizer=FakeSynthesizer(),
    ).run(AIRequest(message="테스트"), providers=["openai"])

    assert result.text == "사용 가능한 AI provider가 없습니다."


def test_provider_retries_then_recovers():
    class FlakyProvider(FakeProvider):
        attempts = 0

        def generate(self, prompt: str, *, system: str = "") -> ProviderResult:
            self.attempts += 1
            if self.attempts < 2:
                raise RuntimeError("temporary")
            return ProviderResult(self.name, self.model, self.text)

    provider = FlakyProvider("openai", "재시도 후 정상 응답")
    result = MultiAIOrchestrator(
        registry=ProviderRegistry([provider]),
        synthesizer=FakeSynthesizer(),
    ).run(AIRequest(message="테스트"), providers=["openai"])

    assert provider.attempts == 2
    assert result.evidence[0]["available"] is True


def test_provider_health_blocks_repeated_failures():
    class BrokenProvider(FakeProvider):
        def generate(self, prompt: str, *, system: str = "") -> ProviderResult:
            raise RuntimeError("down")

    provider = BrokenProvider("openai", "")
    orchestrator = MultiAIOrchestrator(
        registry=ProviderRegistry([provider]),
        synthesizer=FakeSynthesizer(),
    )
    orchestrator.max_retries = 0

    for _ in range(3):
        orchestrator.run(AIRequest(message="테스트"), providers=["openai"])

    assert orchestrator.provider_health.allow("openai") is False
    snapshot = orchestrator.provider_health.snapshot()["openai"]
    assert snapshot["failures"] == 3
    assert snapshot["blocked"] is True


def test_adaptive_selection_learns_from_results():
    registry = ProviderRegistry([
        FakeProvider("openai", "충분히 긴 분석 결과입니다. " * 8),
        FakeProvider("deepseek", "짧은 결과"),
        FakeProvider("perplexity", "시장 분석 결과입니다. " * 8),
    ])
    orchestrator = MultiAIOrchestrator(
        registry=registry,
        synthesizer=FakeSynthesizer(),
    )
    first = orchestrator.run(
        AIRequest(message="최근 시장을 분석해줘", use_case="intelligence")
    )
    assert len(first.evidence) == 3
    assert 1 <= len(orchestrator.adaptive_router.performance) <= 3
    second = orchestrator.run(
        AIRequest(message="최근 시장을 분석해줘", use_case="intelligence")
    )
    assert len(second.evidence) <= 3


def test_adaptive_selection_skips_blocked_name():
    registry = ProviderRegistry([
        FakeProvider("openai", "정상 결과"),
        FakeProvider("perplexity", "정상 결과"),
    ])
    orchestrator = MultiAIOrchestrator(
        registry=registry,
        synthesizer=FakeSynthesizer(),
    )
    orchestrator.provider_health.failure("openai", "down")
    orchestrator.provider_health.failure("openai", "down")
    orchestrator.provider_health.failure("openai", "down")
    result = orchestrator.run(
        AIRequest(message="최근 시장을 분석해줘", use_case="intelligence")
    )
    assert all(item["provider"] != "openai" or not item["available"] for item in result.evidence)


def test_adaptive_routing_prefers_lower_relative_cost_when_quality_is_equal():
    registry = ProviderRegistry([
        FakeProvider("openai", "동일한 충분한 분석 결과입니다. " * 8),
        FakeProvider("deepseek", "동일한 충분한 분석 결과입니다. " * 8),
    ])
    orchestrator = MultiAIOrchestrator(registry=registry, synthesizer=FakeSynthesizer())
    candidates = ["openai", "deepseek"]
    selected = orchestrator._adaptive_names(
        AIRequest(message="일반 분석", use_case="chat"), candidates
    )
    assert selected == ["deepseek"]

def test_adaptive_routing_uses_capability_signal():
    registry = ProviderRegistry([
        FakeProvider("openai", "일반 분석"),
        FakeProvider("perplexity", "최신 시장 뉴스"),
    ])
    orchestrator = MultiAIOrchestrator(registry=registry, synthesizer=FakeSynthesizer())
    selected = orchestrator._adaptive_names(
        AIRequest(message="오늘 최신 시장 뉴스를 확인해줘", use_case="chat"),
        ["openai", "perplexity"],
    )
    assert selected == ["perplexity"]


def test_adaptive_routing_uses_korean_specialist_signal():
    registry = ProviderRegistry([
        FakeProvider("openai", "일반 분석"),
        FakeProvider("naver", "한국 시장 분석"),
    ])
    orchestrator = MultiAIOrchestrator(registry=registry, synthesizer=FakeSynthesizer())
    selected = orchestrator._adaptive_names(
        AIRequest(message="한국 시장 경쟁사 동향을 분석해줘", use_case="chat"),
        ["openai", "naver"],
    )
    assert selected == ["naver"]
