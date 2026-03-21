"""Tests for configuration loading."""

from pathlib import Path

from hirekit.core.config import HireKitConfig, load_config


class TestConfig:
    def test_default_config(self):
        config = HireKitConfig()
        assert config.analysis.default_region == "kr"
        assert config.llm.provider == "none"
        assert config.analysis.cache_ttl_hours == 168

    def test_load_missing_file_returns_defaults(self, tmp_path):
        config = load_config(tmp_path / "nonexistent.toml")
        assert config.analysis.default_region == "kr"

    def test_load_config_from_file(self, tmp_path):
        config_file = tmp_path / "config.toml"
        config_file.write_text("""
[analysis]
default_region = "us"
cache_ttl_hours = 24

[llm]
provider = "openai"
model = "gpt-4o"
""")
        config = load_config(config_file)
        assert config.analysis.default_region == "us"
        assert config.analysis.cache_ttl_hours == 24
        assert config.llm.provider == "openai"
        assert config.llm.model == "gpt-4o"

    def test_default_sources(self):
        config = HireKitConfig()
        assert "dart" in config.sources.enabled
        assert "github" in config.sources.enabled
