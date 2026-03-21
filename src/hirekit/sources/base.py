"""Base protocol for all data source plugins."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class SourceResult:
    """Standardized output from any data source."""

    source_name: str
    section: str  # maps to report section (e.g., "overview", "financials", "culture", "tech")
    data: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0  # 0.0-1.0
    collected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    url: str = ""  # provenance URL
    raw: str = ""  # raw text for LLM consumption

    @property
    def is_stale(self) -> bool:
        """Check if data is older than 90 days."""
        collected = datetime.fromisoformat(self.collected_at)
        return (datetime.now(timezone.utc) - collected).days > 90


class BaseSource(ABC):
    """All data source plugins implement this protocol.

    To create a custom source plugin:
        1. Subclass BaseSource
        2. Set class attributes (name, region, sections)
        3. Implement is_available() and collect()
        4. Register via entry_points in pyproject.toml or @SourceRegistry.register
    """

    name: str = ""
    region: str = "global"  # "kr", "us", "global"
    sections: list[str] = []
    requires_api_key: bool = False
    api_key_env_var: str = ""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if API keys / dependencies are present."""
        ...

    @abstractmethod
    def collect(self, company: str, **kwargs: Any) -> list[SourceResult]:
        """Collect data for a given company. Return empty list on failure, never raise."""
        ...

    def get_timeout(self) -> int:
        """Per-source timeout in seconds. Override for slow sources."""
        return 30


class SourceRegistry:
    """Plugin registry with auto-discovery via entry_points."""

    _sources: dict[str, type[BaseSource]] = {}

    @classmethod
    def register(cls, source_class: type[BaseSource]) -> type[BaseSource]:
        """Register a source class. Can be used as a decorator."""
        cls._sources[source_class.name] = source_class
        return source_class

    @classmethod
    def get_all(cls) -> dict[str, type[BaseSource]]:
        return dict(cls._sources)

    @classmethod
    def get_available(cls, region: str | None = None) -> list[BaseSource]:
        """Return instantiated sources that have their dependencies met."""
        sources = [s() for s in cls._sources.values()]
        if region:
            sources = [s for s in sources if s.region == region]
        return [s for s in sources if s.is_available()]

    @classmethod
    def discover_plugins(cls) -> None:
        """Load user plugins from entry_points group 'hirekit.sources'."""
        from importlib.metadata import entry_points

        for ep in entry_points(group="hirekit.sources"):
            try:
                ep.load()
            except Exception:
                pass  # graceful skip for broken plugins
