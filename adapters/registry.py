from dataclasses import dataclass
from .base import PlatformAdapter

@dataclass(frozen=True)
class AdapterDescriptor:
    country_code: str
    platform: str
    categories: tuple[str, ...]
    capabilities: tuple[str, ...]

class AdapterRegistry:
    def __init__(self): self._adapters: dict[tuple[str,str], PlatformAdapter] = {}
    def register(self, country_code: str, platform: str, adapter: PlatformAdapter):
        self._adapters[(country_code.upper(), platform.lower())] = adapter
    def get(self, country_code: str, platform: str):
        return self._adapters.get((country_code.upper(), platform.lower()))
    def supported(self): return list(self._adapters)
