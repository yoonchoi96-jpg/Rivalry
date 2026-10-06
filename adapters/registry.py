from dataclasses import dataclass

from .base import PlatformAdapter


@dataclass(frozen=True)
class AdapterDescriptor:
    country_code: str
    platform: str
    categories: tuple[str, ...]
    capabilities: tuple[str, ...]


class AdapterRegistry:
    def __init__(self) -> None:
        self._adapters: dict[tuple[str, str], PlatformAdapter] = {}
        self._source_adapters: dict[str, PlatformAdapter] = {}

    def register(self, country_code: str, platform: str, adapter: PlatformAdapter) -> None:
        self._adapters[(country_code.upper(), platform.lower())] = adapter

    def register_source(self, source_id: str, adapter: PlatformAdapter) -> None:
        self._source_adapters[source_id] = adapter

    def get(self, country_code: str, platform: str) -> PlatformAdapter | None:
        return self._adapters.get((country_code.upper(), platform.lower())) or self._adapters.get(("GLOBAL", platform.lower()))

    def get_source(self, source_id: str) -> PlatformAdapter | None:
        return self._source_adapters.get(source_id)

    def supported(self) -> list[tuple[str, str]]:
        return list(self._adapters)
