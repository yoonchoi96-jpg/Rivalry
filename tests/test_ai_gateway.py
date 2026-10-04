from types import SimpleNamespace

from core.ai.gateway import OpenAIGateway
from core.ai.models import AIRequest, AIUseCase


class FakeResponses:
    def __init__(self):
        self.last = None

    def create(self, **kwargs):
        self.last = kwargs
        return SimpleNamespace(
            id="resp_test",
            output_text="테스트 응답",
            usage=SimpleNamespace(input_tokens=10, output_tokens=5, total_tokens=15),
        )


class FakeClient:
    def __init__(self):
        self.responses = FakeResponses()


def test_gateway_routes_chat_to_default_model():
    client = FakeClient()
    gateway = OpenAIGateway(client=client)

    result = gateway.respond(AIRequest(message="오늘 뭐 달라졌어?"))

    assert result.text == "테스트 응답"
    assert result.model == "gpt-5.6-luna"
    assert client.responses.last["model"] == "gpt-5.6-luna"


def test_gateway_uses_expert_model_and_preserves_tools():
    client = FakeClient()
    gateway = OpenAIGateway(client=client)
    tools = [{"type": "function", "name": "get_today_changes"}]

    result = gateway.respond(
        AIRequest(message="이번 달 매출을 올리려면?", use_case=AIUseCase.EXPERT),
        tools=tools,
    )

    assert result.model == "gpt-5.6-sol"
    assert client.responses.last["tools"] == tools
    assert result.usage["total_tokens"] == 15
