"""Configuration loader for HireKit."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

DEFAULT_CONFIG_DIR = Path.home() / ".hirekit"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.toml"


class LLMConfig(BaseModel):
    provider: str = "none"  # openai, anthropic, ollama, none
    model: str = "gpt-4o-mini"
    temperature: float = 0.3
    max_tokens: int = 4096


class SourcesConfig(BaseModel):
    enabled: list[str] = Field(default_factory=lambda: ["dart", "github", "naver_news"])
    disabled: list[str] = Field(default_factory=list)


class OutputConfig(BaseModel):
    format: str = "markdown"  # markdown, json, terminal
    directory: str = "./reports"
    template: str = "default"


class AnalysisConfig(BaseModel):
    default_region: str = "kr"
    cache_ttl_hours: int = 168  # 7 days
    parallel_workers: int = 5


class HireKitConfig(BaseModel):
    """Root configuration model."""

    analysis: AnalysisConfig = Field(default_factory=AnalysisConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    sources: SourcesConfig = Field(default_factory=SourcesConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)


def load_config(config_path: Path | None = None) -> HireKitConfig:
    """Load configuration from TOML file, falling back to defaults."""
    path = config_path or DEFAULT_CONFIG_FILE

    if path.exists():
        with open(path, "rb") as f:
            data: dict[str, Any] = tomllib.load(f)
        return HireKitConfig(**data)

    return HireKitConfig()


def ensure_config_dir() -> Path:
    """Create config directory if it doesn't exist."""
    DEFAULT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return DEFAULT_CONFIG_DIR
