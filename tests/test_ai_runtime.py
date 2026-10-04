from types import SimpleNamespace

from core.ai.models import AIRequest
from core.ai.runtime import AIRuntime


class FakeResponses:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if len(self.calls) == 1:
            call = SimpleNamespace(
                type="function_call",
                name="get_today_changes",
                arguments='{"business_id":"b1","days":1}',
                call_id="call_1",
            )
            return SimpleNamespace(id="resp_1", output=[call], output_text="", usage=None)
        return SimpleNamespace(
            id="resp_2",
            output=[],
            output_text="오늘 중요한 변화는 1건입니다.",
            usage=SimpleNamespace(input_tokens=20, output_tokens=8, total_tokens=28),
        )


class FakeClient:
    def __init__(self):
        self.responses = FakeResponses()


class FakeGateway:
    def __init__(self, client):
        self.client = client

    def model_for(self, use_case):
        return "test-model"

    @staticmethod
    def _instructions(use_case):
        return "test"

    @staticmethod
    def _response_from(response, model):
        from core.ai.models import AIResponse
        return AIResponse(text=response.output_text, model=model, response_id=response.id, usage={
            "input_tokens": getattr(response.usage, "input_tokens", 0),
            "output_tokens": getattr(response.usage, "output_tokens", 0),
            "total_tokens": getattr(response.usage, "total_tokens", 0),
        } if response.usage else {})


def test_runtime_executes_function_call_and_continues():
    client = FakeClient()
    seen = {}

    def today_changes(args):
        seen.update(args)
        return {"changes": [{"id": "c1", "impact_score": 84}]}

    runtime = AIRuntime(
        gateway=FakeGateway(client),
        handlers={"get_today_changes": today_changes},
    )

    result = runtime.run(AIRequest(message="오늘 뭐 달라졌어?"))

    assert seen == {"business_id": "b1", "days": 1}
    assert result.text == "오늘 중요한 변화는 1건입니다."
    assert client.responses.calls[1]["previous_response_id"] == "resp_1"
    assert result.usage["total_tokens"] == 28
