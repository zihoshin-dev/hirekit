"""Tests for source base protocol and registry."""

from hirekit.sources.base import BaseSource, SourceRegistry, SourceResult


class MockSource(BaseSource):
    name = "mock"
    region = "global"
    sections = ["overview"]

    def is_available(self) -> bool:
        return True

    def collect(self, company, **kwargs):
        return [SourceResult(
            source_name=self.name,
            section="overview",
            data={"company": company},
        )]


class UnavailableSource(BaseSource):
    name = "unavailable"
    region = "kr"
    sections = ["tech"]

    def is_available(self) -> bool:
        return False

    def collect(self, company, **kwargs):
        return []


class TestSourceRegistry:
    def setup_method(self):
        # Clear registry before each test
        SourceRegistry._sources = {}

    def test_register_source(self):
        SourceRegistry.register(MockSource)
        assert "mock" in SourceRegistry.get_all()

    def test_get_available_filters_unavailable(self):
        SourceRegistry.register(MockSource)
        SourceRegistry.register(UnavailableSource)
        available = SourceRegistry.get_available()
        names = [s.name for s in available]
        assert "mock" in names
        assert "unavailable" not in names

    def test_get_available_by_region(self):
        SourceRegistry.register(MockSource)
        SourceRegistry.register(UnavailableSource)
        kr_sources = SourceRegistry.get_available(region="kr")
        assert len(kr_sources) == 0  # UnavailableSource is kr but not available

        global_sources = SourceRegistry.get_available(region="global")
        assert len(global_sources) == 1


class TestSourceResult:
    def test_stale_detection(self):
        result = SourceResult(
            source_name="test",
            section="overview",
            collected_at="2025-01-01T00:00:00+00:00",
        )
        assert result.is_stale  # More than 90 days ago

    def test_fresh_result(self):
        result = SourceResult(source_name="test", section="overview")
        assert not result.is_stale  # Just created


class TestMockSourceCollection:
    def test_collect_returns_results(self):
        source = MockSource()
        results = source.collect("TestCorp")
        assert len(results) == 1
        assert results[0].data["company"] == "TestCorp"
        assert results[0].source_name == "mock"
