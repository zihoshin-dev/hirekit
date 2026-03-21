"""Tests for parallel data collection executor."""

import time

import pytest

from hirekit.core.parallel import collect_parallel
from hirekit.sources.base import BaseSource, SourceResult


class FastSource(BaseSource):
    name = "fast"
    region = "global"
    sections = ["overview"]

    def is_available(self) -> bool:
        return True

    def collect(self, company: str, **kwargs) -> list[SourceResult]:
        return [SourceResult(source_name=self.name, section="overview",
                             data={"company": company})]


class SlowSource(BaseSource):
    name = "slow"
    region = "global"
    sections = ["tech"]

    def __init__(self, delay: float = 0.05):
        self._delay = delay

    def get_timeout(self) -> int:
        return 1

    def is_available(self) -> bool:
        return True

    def collect(self, company: str, **kwargs) -> list[SourceResult]:
        time.sleep(self._delay)
        return [SourceResult(source_name=self.name, section="tech",
                             data={"slow": True})]


class FailingSource(BaseSource):
    name = "failing"
    region = "global"
    sections = ["overview"]

    def is_available(self) -> bool:
        return True

    def collect(self, company: str, **kwargs) -> list[SourceResult]:
        raise RuntimeError("API is down")


class EmptySource(BaseSource):
    name = "empty"
    region = "global"
    sections = ["overview"]

    def is_available(self) -> bool:
        return True

    def collect(self, company: str, **kwargs) -> list[SourceResult]:
        return []


class TestCollectParallel:
    def test_returns_results_from_available_sources(self):
        sources = [FastSource()]
        results = collect_parallel(sources, "카카오")
        assert len(results) == 1
        assert results[0].source_name == "fast"

    def test_failing_source_skipped_not_raised(self):
        sources = [FastSource(), FailingSource()]
        results = collect_parallel(sources, "카카오")
        # FailingSource raises — should be skipped, FastSource still returns
        source_names = [r.source_name for r in results]
        assert "fast" in source_names
        assert "failing" not in source_names

    def test_empty_source_returns_no_results(self):
        sources = [EmptySource()]
        results = collect_parallel(sources, "카카오")
        assert results == []

    def test_multiple_sources_all_collected(self):
        sources = [FastSource(), SlowSource(delay=0.01), EmptySource()]
        results = collect_parallel(sources, "네이버", max_workers=3)
        source_names = {r.source_name for r in results}
        assert "fast" in source_names
        assert "slow" in source_names

    def test_empty_sources_list_returns_empty(self):
        results = collect_parallel([], "카카오")
        assert results == []

    def test_company_name_passed_to_source(self):
        sources = [FastSource()]
        results = collect_parallel(sources, "토스")
        assert results[0].data["company"] == "토스"

    def test_parallel_faster_than_sequential(self):
        """Two 50ms sources should finish in ~50ms with parallelism, not ~100ms."""
        sources = [SlowSource(delay=0.05), SlowSource(delay=0.05)]
        # Give each a unique name to avoid conflict
        sources[0].name = "slow1"
        sources[1].name = "slow2"

        start = time.perf_counter()
        results = collect_parallel(sources, "카카오", max_workers=2)
        elapsed = time.perf_counter() - start

        assert len(results) == 2
        assert elapsed < 0.15  # well under 100ms sequential time

    def test_max_workers_respected(self):
        """Should not crash with max_workers=1 (sequential fallback)."""
        sources = [FastSource(), EmptySource()]
        results = collect_parallel(sources, "카카오", max_workers=1)
        assert any(r.source_name == "fast" for r in results)
