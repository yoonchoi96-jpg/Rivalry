from core.ai.models import AIRequest, AIUseCase
from core.ai.router import AIRouter


def test_chat_uses_single_provider():
    decision = AIRouter().select(AIRequest(message="안녕", use_case=AIUseCase.CHAT))
    assert decision.providers == ["openai"]


def test_korean_latest_research_adds_naver_and_perplexity():
    decision = AIRouter().select(
        AIRequest(
            message="최근 한국 시장에서 경쟁사 가격이 왜 올랐는지 분석해줘",
            use_case=AIUseCase.INTELLIGENCE,
        )
    )
    assert "perplexity" in decision.providers
    assert "naver" in decision.providers


def test_china_social_analysis_adds_qwen_and_grok():
    decision = AIRouter().select(
        AIRequest(
            message="중국 시장에서 SNS 바이럴 전략의 원인을 분석해줘",
            use_case=AIUseCase.EXPERT,
        )
    )
    assert "qwen" in decision.providers
    assert "grok" in decision.providers
