from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class ProviderResult:
    provider: str
    model: str
    text: str
    available: bool = True
    error: str | None = None


class AIProvider(ABC):
    name: str

    @abstractmethod
    def generate(self, prompt: str, *, system: str = "") -> ProviderResult:
        raise NotImplementedError


class OpenAIProvider(AIProvider):
    name = "openai"

    def __init__(self, client: Any | None = None, model: str | None = None):
        self._client = client
        self.model = model or os.getenv("RIVALRY_AI_OPENAI_RESEARCH_MODEL", "gpt-6-luna")

    @property
    def client(self) -> Any:
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        return self._client

    def generate(self, prompt: str, *, system: str = "") -> ProviderResult:
        response = self.client.responses.create(
            model=self.model,
            instructions=system or None,
            input=prompt,
        )
        return ProviderResult(self.name, self.model, getattr(response, "output_text", ""))


class ClaudeProvider(AIProvider):
    name = "claude"

    def __init__(self, client: Any | None = None, model: str | None = None):
        self._client = client
        self.model = model or os.getenv("RIVALRY_AI_CLAUDE_MODEL", "claude-opus-5-5")

    @property
    def client(self) -> Any:
        if self._client is None:
            from anthropic import Anthropic
            self._client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        return self._client

    def generate(self, prompt: str, *, system: str = "") -> ProviderResult:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=int(os.getenv("RIVALRY_AI_CLAUDE_MAX_TOKENS", "4096")),
            system=system or None,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "\n".join(
            block.text for block in getattr(response, "content", [])
            if getattr(block, "type", "") == "text"
        )
        return ProviderResult(self.name, self.model, text)


class OpenAICompatibleProvider(AIProvider):
    """Provider adapter for APIs exposing an OpenAI-compatible Responses API."""

    def __init__(self, name: str, api_key_env: str, base_url: str, model_env: str, default_model: str):
        self.name = name
        self.api_key_env = api_key_env
        self.base_url = base_url
        self.model = os.getenv(model_env, default_model)

    def generate(self, prompt: str, *, system: str = "") -> ProviderResult:
        from openai import OpenAI

        client = OpenAI(
            api_key=os.getenv(self.api_key_env),
            base_url=self.base_url,
        )
        response = client.responses.create(
            model=self.model,
            instructions=system or None,
            input=prompt,
        )
        return ProviderResult(self.name, self.model, getattr(response, "output_text", ""))


class DeepSeekProvider(OpenAICompatibleProvider):
    def __init__(self):
        super().__init__(
            "deepseek",
            "DEEPSEEK_API_KEY",
            os.getenv("RIVALRY_DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            "RIVALRY_AI_DEEPSEEK_MODEL",
            "deepseek-flash",
        )


class GrokProvider(OpenAICompatibleProvider):
    def __init__(self):
        super().__init__(
            "grok",
            "XAI_API_KEY",
            os.getenv("RIVALRY_XAI_BASE_URL", "https://api.x.ai/v1"),
            "RIVALRY_AI_GROK_MODEL",
            "grok-4.7",
        )


class QwenProvider(OpenAICompatibleProvider):
    def __init__(self):
        super().__init__(
            "qwen",
            "QWEN_API_KEY",
            os.getenv("RIVALRY_QWEN_BASE_URL", ""),
            "RIVALRY_AI_QWEN_MODEL",
            "qwen3-max",
        )

    def generate(self, prompt: str, *, system: str = "") -> ProviderResult:
        base_url = self.base_url or os.getenv("DASHSCOPE_BASE_URL", "")
        if not base_url:
            raise RuntimeError("QWEN_API_BASE_URL is not configured")
        self.base_url = base_url
        return super().generate(prompt, system=system)


class NaverAIProvider(AIProvider):
    """NAVER CLOVA Studio adapter.

    The endpoint is configurable because CLOVA Studio exposes different
    endpoints by product/region/version. No endpoint is guessed in code.
    """

    name = "naver"

    def __init__(self, model: str | None = None):
        self.model = model or os.getenv("RIVALRY_AI_NAVER_MODEL", "HCX-005")
        self.endpoint = os.getenv("NAVER_AI_API_URL", "")

    def generate(self, prompt: str, *, system: str = "") -> ProviderResult:
        if not self.endpoint:
            raise RuntimeError("NAVER_AI_API_URL is not configured")
        api_key = os.getenv("NAVER_AI_API_KEY")
        if not api_key:
            raise RuntimeError("NAVER_AI_API_KEY is not configured")

        payload = {
            "messages": [
                *([{"role": "system", "content": system}] if system else []),
                {"role": "user", "content": prompt},
            ],
        }
        request = Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urlopen(request, timeout=float(os.getenv("RIVALRY_AI_NAVER_TIMEOUT", "30"))) as response:
            data = json.loads(response.read().decode("utf-8"))

        text = data.get("result", {}).get("message", {}).get("content")
        if text is None:
            text = data.get("output_text", data.get("text", ""))
        return ProviderResult(self.name, self.model, str(text))


class GeminiProvider(AIProvider):
    name = "gemini"

    def __init__(self, client: Any | None = None, model: str | None = None):
        self._client = client
        self.model = model or os.getenv("RIVALRY_AI_GEMINI_MODEL", "gemini-3.5-flash")

    @property
    def client(self) -> Any:
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        return self._client

    def generate(self, prompt: str, *, system: str = "") -> ProviderResult:
        config = {"system_instruction": system} if system else None
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config,
        )
        return ProviderResult(self.name, self.model, getattr(response, "text", ""))


class PerplexityProvider(AIProvider):
    name = "perplexity"

    def __init__(self, client: Any | None = None, model: str | None = None):
        self._client = client
        self.model = model or os.getenv("RIVALRY_AI_PERPLEXITY_MODEL", "sonar-pro")

    @property
    def client(self) -> Any:
        if self._client is None:
            from perplexity import Perplexity
            self._client = Perplexity(api_key=os.getenv("PERPLEXITY_API_KEY"))
        return self._client

    def generate(self, prompt: str, *, system: str = "") -> ProviderResult:
        response = self.client.responses.create(
            preset=os.getenv("RIVALRY_PERPLEXITY_PRESET", "pro-search"),
            input=prompt,
            instructions=system or None,
        )
        return ProviderResult(self.name, self.model, getattr(response, "output_text", ""))


class ProviderRegistry:
    """Central registry for independent AI providers.

    Providers are optional. Missing credentials/configuration produce an
    unavailable result at the orchestrator boundary rather than fake data.
    """

    def __init__(self, providers: list[AIProvider] | None = None):
        self.providers = providers if providers is not None else [
            OpenAIProvider(),
            ClaudeProvider(),
            GeminiProvider(),
            PerplexityProvider(),
            DeepSeekProvider(),
            NaverAIProvider(),
            GrokProvider(),
            QwenProvider(),
        ]

    def by_name(self, name: str) -> AIProvider:
        for provider in self.providers:
            if provider.name == name:
                return provider
        raise KeyError(f"Unknown AI provider: {name}")

    def available_names(self) -> list[str]:
        return [provider.name for provider in self.providers]
