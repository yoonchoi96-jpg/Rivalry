from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


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
        self.model = model or os.getenv("RIVALRY_AI_OPENAI_RESEARCH_MODEL", "gpt-5.6-luna")

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


class GeminiProvider(AIProvider):
    name = "gemini"

    def __init__(self, client: Any | None = None, model: str | None = None):
        self._client = client
        self.model = model or os.getenv("RIVALRY_AI_GEMINI_MODEL", "gemini-3.8-flash")

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

    Providers are optional. Missing API keys or SDKs never become fake data;
    callers receive an unavailable result and can decide whether to fall back.
    """

    def __init__(self, providers: list[AIProvider] | None = None):
        self.providers = providers or [
            OpenAIProvider(),
            GeminiProvider(),
            PerplexityProvider(),
        ]

    def by_name(self, name: str) -> AIProvider:
        for provider in self.providers:
            if provider.name == name:
                return provider
        raise KeyError(f"Unknown AI provider: {name}")

    def available_names(self) -> list[str]:
        return [provider.name for provider in self.providers]
