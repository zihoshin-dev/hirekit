"""Tests for CompanyAnalyzer orchestrator and AnalysisReport."""

from typing import Any, cast
from unittest.mock import MagicMock, patch

from hirekit.core.config import HireKitConfig
from hirekit.engine.company_analyzer import AnalysisReport, CompanyAnalyzer
from hirekit.engine.scorer import create_default_scorecard
from hirekit.llm.base import NoLLM
from hirekit.sources.base import SourceRegistry, SourceResult

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_report(
    company: str = "카카오",
    region: str = "kr",
    tier: int = 1,
    sections: dict[int, dict[str, Any]] | None = None,
    score: float = 3.0,
) -> AnalysisReport:
    scorecard = create_default_scorecard(company)
    for dim in scorecard.dimensions:
        dim.score = score
    return AnalysisReport(
        company=company,
        region=region,
        tier=tier,
        sections=sections or {},
        scorecard=scorecard,
    )


# ---------------------------------------------------------------------------
# AnalysisReport serialization
# ---------------------------------------------------------------------------

class TestAnalysisReportToDict:
    def test_to_dict_contains_required_keys(self):
        report = make_report()
        d = report.to_dict()
        for key in ("company", "region", "tier", "sections", "scorecard", "sources"):
            assert key in d

    def test_to_dict_company_name_preserved(self):
        report = make_report(company="토스")
        assert report.to_dict()["company"] == "토스"

    def test_to_dict_scorecard_includes_total_and_grade(self):
        report = make_report(score=4.0)
        sc = report.to_dict()["scorecard"]
        assert "total" in sc
        assert "grade" in sc
        assert sc["total"] > 0

    def test_to_dict_sources_list_from_source_results(self):
        report = make_report()
        report.source_results = [
            SourceResult(source_name="dart", section="overview",
                         url="https://dart.fss.or.kr/"),
        ]
        sources = report.to_dict()["sources"]
        assert len(sources) == 1
        assert sources[0]["name"] == "dart"

    def test_to_dict_sources_include_lineage_fields(self):
        report = make_report()
        report.source_results = [
            SourceResult(
                source_name="dart",
                section="overview",
                url="https://dart.fss.or.kr/",
                collected_at="2026-03-22T00:00:00+00:00",
                effective_at="2026-03-21T00:00:00+00:00",
                confidence=0.9,
            ),
        ]
        source = report.to_dict()["sources"][0]
        assert source["evidence_id"].startswith("dart:overview:")
        assert source["collected_at"] == "2026-03-22T00:00:00+00:00"
        assert source["effective_at"] == "2026-03-21T00:00:00+00:00"
        assert source["confidence"] == 0.9
        assert source["trust_label"] == "verified"
        assert source["publication_boundary"] == "internal_only"

    def test_to_dict_scorecard_dimensions_include_source_key(self):
        report = make_report()
        assert report.scorecard is not None
        report.scorecard.dimensions[0].source = "dart:overview:20260322T000000+0000"
        dimension = report.to_dict()["scorecard"]["dimensions"][0]
        assert dimension["source"] == "dart:overview:20260322T000000+0000"

    def test_to_dict_no_scorecard_gives_zero_total(self):
        report = AnalysisReport(company="테스트", region="kr", tier=1)
        d = report.to_dict()
        assert d["scorecard"]["total"] == 0
        assert d["scorecard"]["grade"] == "N/A"


class TestAnalysisReportToMarkdown:
    def test_to_markdown_returns_string(self):
        report = make_report()
        md = report.to_markdown()
        assert isinstance(md, str)
        assert len(md) > 0

    def test_to_markdown_contains_company_name(self):
        report = make_report(company="네이버")
        assert "네이버" in report.to_markdown()


class TestAnalysisReportToRich:
    def test_to_rich_returns_panel(self):
        from rich.panel import Panel
        report = make_report()
        panel = report.to_rich()
        assert isinstance(panel, Panel)


# ---------------------------------------------------------------------------
# CompanyAnalyzer initialization
# ---------------------------------------------------------------------------

class TestCompanyAnalyzerInit:
    def test_init_with_no_llm_flag(self):
        config = HireKitConfig()
        analyzer = CompanyAnalyzer(config=config, use_llm=False)
        assert isinstance(analyzer.llm, NoLLM)

    def test_init_with_none_provider_gives_nollm(self):
        config = HireKitConfig()
        config.llm.provider = "none"
        analyzer = CompanyAnalyzer(config=config, use_llm=True)
        assert isinstance(analyzer.llm, NoLLM)

    def test_cache_ttl_from_config(self):
        config = HireKitConfig()
        config.analysis.cache_ttl_hours = 24
        analyzer = CompanyAnalyzer(config=config, use_llm=False)
        assert analyzer.cache.ttl_seconds == 24 * 3600


# ---------------------------------------------------------------------------
# CompanyAnalyzer.analyze — with mocked sources
# ---------------------------------------------------------------------------

class MockCollectSource:
    name = "mock_dart"
    region = "kr"

    def is_available(self):
        return True

    def get_timeout(self):
        return 10

    def collect(self, company, **kwargs):
        return [
            SourceResult(
                source_name="mock_dart",
                section="overview",
                data={"company_name": company, "ceo": "홍길동"},
                raw=f"{company} overview data",
            )
        ]


class TestCompanyAnalyzerAnalyze:
    def setup_method(self):
        SourceRegistry._sources = {}

    def _make_analyzer(self) -> "CompanyAnalyzer":
        """Return an analyzer with cache bypassed to avoid cross-test pollution."""
        config = HireKitConfig()
        analyzer = CompanyAnalyzer(config=config, use_llm=False)
        analyzer.cache.get = MagicMock(return_value=None)
        analyzer.cache.set = MagicMock()
        return analyzer

    def test_analyze_returns_analysis_report(self):
        analyzer = self._make_analyzer()

        with patch("hirekit.engine.company_analyzer.collect_parallel",
                   return_value=[SourceResult(
                       source_name="mock", section="overview",
                       data={"company_name": "카카오"},
                       raw="overview",
                   )]):
            with patch.object(SourceRegistry, "get_available", return_value=[]):
                with patch.object(SourceRegistry, "discover_plugins"):
                    report = analyzer.analyze("카카오")

        assert isinstance(report, AnalysisReport)
        assert report.company == "카카오"

    def test_analyze_creates_scorecard(self):
        analyzer = self._make_analyzer()

        with patch("hirekit.engine.company_analyzer.collect_parallel", return_value=[]):
            with patch.object(SourceRegistry, "get_available", return_value=[]):
                with patch.object(SourceRegistry, "discover_plugins"):
                    report = analyzer.analyze("네이버")

        assert report.scorecard is not None
        assert len(report.scorecard.dimensions) == 5

    def test_analyze_groups_results_by_section(self):
        analyzer = self._make_analyzer()

        fake_results = [
            SourceResult(source_name="dart", section="overview",
                         data={"company_name": "토스"}),
            SourceResult(source_name="github", section="tech",
                         data={"total_score": 75}),
        ]

        # Patch collect_parallel where it is used inside company_analyzer
        with patch("hirekit.engine.company_analyzer.collect_parallel",
                   return_value=fake_results):
            with patch.object(SourceRegistry, "get_available", return_value=[]):
                with patch.object(SourceRegistry, "discover_plugins"):
                    report = analyzer.analyze("토스")

        # overview → section 1, tech → section 7
        assert 1 in report.sections
        assert 7 in report.sections

    def test_analyze_skips_disabled_sources(self):
        config = HireKitConfig()
        config.sources.disabled = ["dart"]
        analyzer = CompanyAnalyzer(config=config, use_llm=False)
        # Force cache miss so collect_parallel is always invoked
        analyzer.cache.get = MagicMock(return_value=None)
        analyzer.cache.set = MagicMock()

        mock_dart = MagicMock()
        mock_dart.name = "dart"
        mock_dart.is_available.return_value = True

        mock_github = MagicMock()
        mock_github.name = "github"
        mock_github.is_available.return_value = True

        with patch.object(SourceRegistry, "get_available",
                          return_value=[mock_dart, mock_github]):
            with patch.object(SourceRegistry, "discover_plugins"):
                with patch("hirekit.engine.company_analyzer.collect_parallel",
                           return_value=[]) as mock_parallel:
                    analyzer.analyze("카카오")

        assert mock_parallel.called
        called_sources = mock_parallel.call_args.kwargs.get(
            "sources", mock_parallel.call_args.args[0] if mock_parallel.call_args.args else []
        )
        assert all(s.name != "dart" for s in called_sources)

    def test_analyze_returns_cached_result_on_second_call(self):
        config = HireKitConfig()
        analyzer = CompanyAnalyzer(config=config, use_llm=False)

        call_count = [0]

        def fake_collect(*args, **kwargs):
            call_count[0] += 1
            return []

        # Use cache.get mock: first call returns None (miss), second returns sentinel
        cache_store: dict[str, Any] = {}

        def mock_cache_get(key):
            return cache_store.get(key)

        def mock_cache_set(key, value):
            cache_store[key] = value

        analyzer.cache.get = mock_cache_get
        analyzer.cache.set = mock_cache_set

        with patch("hirekit.engine.company_analyzer.collect_parallel",
                   side_effect=fake_collect):
            with patch.object(SourceRegistry, "get_available", return_value=[]):
                with patch.object(SourceRegistry, "discover_plugins"):
                    analyzer.analyze("카카오", region="kr", tier=1)
                    analyzer.analyze("카카오", region="kr", tier=1)

        # collect_parallel called only once (second call hits cache)
        assert call_count[0] == 1

    def test_cached_result_restores_scorecard_and_source_results(self):
        config = HireKitConfig()
        analyzer = CompanyAnalyzer(config=config, use_llm=False)

        cache_store: dict[str, Any] = {}

        def mock_cache_get(key):
            return cache_store.get(key)

        def mock_cache_set(key, value):
            cache_store[key] = value

        analyzer.cache.get = mock_cache_get
        analyzer.cache.set = mock_cache_set

        fake_results = [
            SourceResult(
                source_name="dart",
                section="overview",
                data={
                    "financials": [
                        {
                            "account": "매출액",
                            "current_amount": "1200000",
                            "previous_amount": "1000000",
                        },
                    ],
                },
                url="https://dart.fss.or.kr/",
                collected_at="2026-03-22T00:00:00+00:00",
                effective_at="2026-03-21T00:00:00+00:00",
            ),
        ]

        with patch("hirekit.engine.company_analyzer.collect_parallel",
                   return_value=fake_results):
            with patch.object(SourceRegistry, "get_available", return_value=[]):
                with patch.object(SourceRegistry, "discover_plugins"):
                    first = analyzer.analyze("카카오", region="kr", tier=1)
                    second = analyzer.analyze("카카오", region="kr", tier=1)

        assert first.scorecard is not None
        assert second.scorecard is not None
        assert second.source_results
        assert second.source_results[0].evidence_id.startswith("dart:overview:")
        assert second.scorecard.dimensions[0].confidence == first.scorecard.dimensions[0].confidence
        assert second.scorecard.dimensions[0].source == first.scorecard.dimensions[0].source

    def test_analyze_caches_serialized_provenance_fields(self):
        analyzer = self._make_analyzer()

        fake_results = [
            SourceResult(
                source_name="dart",
                section="overview",
                data={"company_name": "카카오"},
                url="https://dart.fss.or.kr/",
                collected_at="2026-03-22T00:00:00+00:00",
                effective_at="2026-03-21T00:00:00+00:00",
            ),
        ]

        with patch("hirekit.engine.company_analyzer.collect_parallel",
                   return_value=fake_results):
            with patch.object(SourceRegistry, "get_available", return_value=[]):
                with patch.object(SourceRegistry, "discover_plugins"):
                    analyzer.analyze("카카오")

        cache_set = cast(MagicMock, analyzer.cache.set)
        cached_payload = cache_set.call_args.args[1]
        source = cached_payload["sources"][0]
        assert source["url"] == "https://dart.fss.or.kr/"
        assert source["collected_at"] == "2026-03-22T00:00:00+00:00"
        assert source["effective_at"] == "2026-03-21T00:00:00+00:00"
        assert source["evidence_id"].startswith("dart:overview:")

    def test_cache_hit_preserves_scorecard(self):
        """캐시 히트 시 scorecard가 보존되는지 확인."""
        config = HireKitConfig()
        analyzer = CompanyAnalyzer(config=config, use_llm=False)

        cache_store: dict[str, Any] = {}
        analyzer.cache.get = lambda k: cache_store.get(k)
        analyzer.cache.set = lambda k, v: cache_store.__setitem__(k, v)

        fake_results = [
            SourceResult(
                source_name="dart",
                section="overview",
                data={
                    "financials": [
                        {"account": "매출액", "current_amount": "1200000",
                         "previous_amount": "1000000"},
                    ],
                },
            ),
        ]

        with patch("hirekit.engine.company_analyzer.collect_parallel",
                   return_value=fake_results):
            with patch.object(SourceRegistry, "get_available", return_value=[]):
                with patch.object(SourceRegistry, "discover_plugins"):
                    first = analyzer.analyze("카카오", region="kr", tier=1)
                    second = analyzer.analyze("카카오", region="kr", tier=1)

        assert second.scorecard is not None
        assert len(second.scorecard.dimensions) == len(first.scorecard.dimensions)
        for d1, d2 in zip(first.scorecard.dimensions, second.scorecard.dimensions):
            assert d2.name == d1.name
            assert d2.score == d1.score
            assert d2.evidence == d1.evidence
            assert d2.confidence == d1.confidence
            assert d2.source == d1.source

    def test_cache_hit_preserves_source_results(self):
        """캐시 히트 시 source_results가 보존되는지 확인."""
        config = HireKitConfig()
        analyzer = CompanyAnalyzer(config=config, use_llm=False)

        cache_store: dict[str, Any] = {}
        analyzer.cache.get = lambda k: cache_store.get(k)
        analyzer.cache.set = lambda k, v: cache_store.__setitem__(k, v)

        fake_results = [
            SourceResult(
                source_name="dart",
                section="overview",
                data={"company_name": "카카오"},
                url="https://dart.fss.or.kr/",
                collected_at="2026-03-22T00:00:00+00:00",
                effective_at="2026-03-21T00:00:00+00:00",
                confidence=0.9,
            ),
            SourceResult(
                source_name="github",
                section="tech",
                data={"total_score": 75},
            ),
        ]

        with patch("hirekit.engine.company_analyzer.collect_parallel",
                   return_value=fake_results):
            with patch.object(SourceRegistry, "get_available", return_value=[]):
                with patch.object(SourceRegistry, "discover_plugins"):
                    analyzer.analyze("카카오", region="kr", tier=1)
                    second = analyzer.analyze("카카오", region="kr", tier=1)

        assert len(second.source_results) == 2
        dart_result = next(r for r in second.source_results if r.source_name == "dart")
        assert dart_result.url == "https://dart.fss.or.kr/"
        assert dart_result.collected_at == "2026-03-22T00:00:00+00:00"
        assert dart_result.effective_at == "2026-03-21T00:00:00+00:00"
        assert dart_result.confidence == 0.9
        assert dart_result.evidence_id.startswith("dart:overview:")

    def test_cache_hit_miss_parity(self):
        """캐시 히트와 미스의 결과가 동등한지 전체 비교."""
        config = HireKitConfig()
        analyzer = CompanyAnalyzer(config=config, use_llm=False)

        cache_store: dict[str, Any] = {}
        analyzer.cache.get = lambda k: cache_store.get(k)
        analyzer.cache.set = lambda k, v: cache_store.__setitem__(k, v)

        fake_results = [
            SourceResult(
                source_name="dart",
                section="overview",
                data={
                    "financials": [
                        {"account": "매출액", "current_amount": "1500000",
                         "previous_amount": "1000000"},
                    ],
                    "employees": [
                        {"headcount": "1000", "avg_salary": "65",
                         "avg_tenure_year": "5"},
                    ],
                },
                url="https://dart.fss.or.kr/",
                collected_at="2026-03-22T00:00:00+00:00",
            ),
        ]

        with patch("hirekit.engine.company_analyzer.collect_parallel",
                   return_value=fake_results):
            with patch.object(SourceRegistry, "get_available", return_value=[]):
                with patch.object(SourceRegistry, "discover_plugins"):
                    miss = analyzer.analyze("카카오", region="kr", tier=1)
                    hit = analyzer.analyze("카카오", region="kr", tier=1)

        # Top-level fields
        assert hit.company == miss.company
        assert hit.region == miss.region
        assert hit.tier == miss.tier
        assert hit.sections == miss.sections

        # Scorecard parity
        assert hit.scorecard is not None
        assert miss.scorecard is not None
        assert hit.scorecard.total_score == miss.scorecard.total_score
        assert hit.scorecard.grade == miss.scorecard.grade
        assert len(hit.scorecard.dimensions) == len(miss.scorecard.dimensions)

        # Source results parity
        assert len(hit.source_results) == len(miss.source_results)
        assert hit.source_results[0].source_name == miss.source_results[0].source_name
        assert hit.source_results[0].section == miss.source_results[0].section
        assert hit.source_results[0].url == miss.source_results[0].url

    def test_analyze_llm_enhance_called_when_available(self):
        config = HireKitConfig()
        analyzer = CompanyAnalyzer(config=config, use_llm=False)

        mock_llm = MagicMock()
        mock_llm.is_available.return_value = True
        analyzer.llm = mock_llm

        # Bypass cache entirely
        analyzer.cache.get = MagicMock(return_value=None)
        analyzer.cache.set = MagicMock()

        fake_results = [
            SourceResult(source_name="mock", section="overview",
                         raw="overview data", data={})
        ]

        enhance_called = [False]

        def fake_enhance(report):
            enhance_called[0] = True
            report.sections.setdefault(1, {})["analysis"] = "LLM overview"

        with patch("hirekit.engine.company_analyzer.collect_parallel",
                   return_value=fake_results):
            with patch.object(SourceRegistry, "get_available", return_value=[]):
                with patch.object(SourceRegistry, "discover_plugins"):
                    with patch.object(analyzer, "_enhance_with_llm",
                                      side_effect=fake_enhance):
                        analyzer.analyze("카카오")

        assert enhance_called[0] is True


# ---------------------------------------------------------------------------
# _score_from_data
# ---------------------------------------------------------------------------

class TestScoreFromData:
    def test_growth_score_from_revenue_growth(self):
        """Revenue growth rate drives growth score, not mere data existence."""
        config = HireKitConfig()
        analyzer = CompanyAnalyzer(config=config, use_llm=False)
        report = make_report(sections={
            1: {"financials": [
                {"account": "매출액", "current_amount": "1,200,000",
                  "previous_amount": "1,000,000"},
            ]}
        })
        analyzer._score_from_data(report)
        assert report.scorecard is not None
        growth_dim = next(d for d in report.scorecard.dimensions if d.name == "growth")
        assert growth_dim.score >= 3.5  # 20% growth
        assert "매출 성장률" in growth_dim.evidence

    def test_growth_score_low_for_declining_revenue(self):
        config = HireKitConfig()
        analyzer = CompanyAnalyzer(config=config, use_llm=False)
        report = make_report(sections={
            1: {"financials": [
                {"account": "매출액", "current_amount": "800,000",
                  "previous_amount": "1,000,000"},
            ]}
        })
        analyzer._score_from_data(report)
        assert report.scorecard is not None
        growth_dim = next(d for d in report.scorecard.dimensions if d.name == "growth")
        assert growth_dim.score <= 2.5  # -20% decline

    def test_compensation_score_from_actual_salary(self):
        """Salary amount drives compensation score."""
        config = HireKitConfig()
        analyzer = CompanyAnalyzer(config=config, use_llm=False)
        report = make_report(sections={
            1: {"employees": [
                {"headcount": "500", "avg_salary": "70",
                  "avg_tenure_year": "5.2", "position": "전체"},
            ]}
        })
        analyzer._score_from_data(report)
        assert report.scorecard is not None
        comp_dim = next(d for d in report.scorecard.dimensions if d.name == "compensation")
        assert comp_dim.score >= 4.0  # 7000만원
        assert "평균 연봉" in comp_dim.evidence

    def test_compensation_score_lower_without_employee_data(self):
        config = HireKitConfig()
        analyzer = CompanyAnalyzer(config=config, use_llm=False)
        report = make_report(sections={1: {}})
        analyzer._score_from_data(report)
        assert report.scorecard is not None
        comp_dim = next(d for d in report.scorecard.dimensions if d.name == "compensation")
        assert comp_dim.score == 2.5

    def test_job_fit_from_github_score(self):
        config = HireKitConfig()
        analyzer = CompanyAnalyzer(config=config, use_llm=False)
        report = make_report()
        report.source_results = [
            SourceResult(source_name="github", section="tech",
                         data={"total_score": 80, "public_repos": 45})
        ]
        report.sections = {7: {}}
        analyzer._score_from_data(report)
        assert report.scorecard is not None
        job_fit = next(d for d in report.scorecard.dimensions if d.name == "job_fit")
        assert job_fit.score >= 4.5  # GitHub score 80 → high
        assert "GitHub 기술 성숙도" in job_fit.evidence

    def test_all_dimension_scores_bounded_0_to_5(self):
        config = HireKitConfig()
        analyzer = CompanyAnalyzer(config=config, use_llm=False)
        report = make_report(sections={
            1: {"financials": [
                {"account": "매출액", "current_amount": "5,000,000",
                 "previous_amount": "3,000,000"},
            ], "employees": [
                {"headcount": "5000", "avg_salary": "90",
                 "avg_tenure_year": "8"},
            ]},
            3: {"strategy": "AI 전략"},
            4: {"naver_blog": [{"title": "후기"}]},
            7: {"tech_stack": ["Python"]},
        })
        report.source_results = [
            SourceResult(source_name="google_news", section="overview", data={}),
            SourceResult(source_name="exa_search", section="culture", data={}),
            SourceResult(source_name="naver_search", section="culture", data={}),
            SourceResult(source_name="github", section="tech",
                         data={"total_score": 90}),
        ]
        analyzer._score_from_data(report)
        assert report.scorecard is not None
        for dim in report.scorecard.dimensions:
            assert 0 <= dim.score <= 5.0, f"{dim.name} score {dim.score} out of range"
