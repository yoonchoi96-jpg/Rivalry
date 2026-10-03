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
            model_copy=lambda update: SimpleNamespace(
                text="통합 판단",
                model=update["model"],
                response_id="final",
                usage={},
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
