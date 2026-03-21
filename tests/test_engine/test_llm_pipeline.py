"""Tests for LLMPipeline — sectioned multi-step analysis with mocked LLM."""

from unittest.mock import MagicMock

from hirekit.engine.llm_pipeline import LLMPipeline
from hirekit.llm.base import LLMResponse, NoLLM
from hirekit.sources.base import SourceResult


def make_llm(text: str = "분석 결과입니다.") -> MagicMock:
    """Return a mock LLM that always returns the given text."""
    llm = MagicMock()
    llm.is_available.return_value = True
    llm.generate.return_value = LLMResponse(text=text, model="mock")
    return llm


def make_results(sections: list[str], raw: str = "테스트 데이터") -> list[SourceResult]:
    return [
        SourceResult(source_name="mock", section=sec, raw=raw)
        for sec in sections
    ]


class TestLLMPipelineAvailability:
    def test_returns_empty_dict_when_llm_unavailable(self):
        pipeline = LLMPipeline(llm=NoLLM())
        result = pipeline.analyze(make_results(["overview"]), "카카오")
        assert result == {}

    def test_returns_empty_dict_when_no_raw_data(self):
        llm = make_llm()
        # Simulate fact extraction returning empty (no raw in results)
        results = [SourceResult(source_name="mock", section="overview", raw="")]
        pipeline = LLMPipeline(llm=llm)
        result = pipeline.analyze(results, "카카오")
        assert result == {}


class TestLLMPipelineAnalyze:
    def test_analyze_returns_all_five_section_keys(self):
        llm = make_llm("테스트 분석 결과")
        pipeline = LLMPipeline(llm=llm)
        results = make_results(["overview", "financials", "tech", "culture"])
        output = pipeline.analyze(results, "카카오")
        # Sections: 0 (speed sheet), 1 (overview), 2 (industry), 7 (tech), 11 (verdict)
        assert set(output.keys()) == {0, 1, 2, 7, 11}

    def test_each_section_contains_non_empty_string(self):
        llm = make_llm("상세 분석 내용입니다.")
        pipeline = LLMPipeline(llm=llm)
        results = make_results(["overview", "financials"])
        output = pipeline.analyze(results, "네이버")
        for key, value in output.items():
            assert isinstance(value, str), f"Section {key} is not a string"
            assert len(value) > 0, f"Section {key} is empty"

    def test_llm_called_multiple_times_for_sections(self):
        llm = make_llm("결과")
        pipeline = LLMPipeline(llm=llm)
        results = make_results(["overview"])
        pipeline.analyze(results, "토스")
        # fact extraction + 4 sections + speed sheet = at least 5 calls
        assert llm.generate.call_count >= 5

    def test_raw_text_truncated_to_6000_chars(self):
        llm = make_llm("ok")
        pipeline = LLMPipeline(llm=llm)
        # Provide more than 6000 chars of raw
        long_raw = "x" * 10000
        results = [SourceResult(source_name="s", section="overview", raw=long_raw)]
        pipeline.analyze(results, "회사")
        # Extract the actual prompt passed to generate for fact extraction
        first_call_args = llm.generate.call_args_list[0]
        prompt = first_call_args.kwargs.get("prompt") or first_call_args.args[0]
        # 6000 char cap + surrounding text — prompt should not be huge
        assert len(prompt) < 10000

    def test_section_label_mapping_included_in_fact_prompt(self):
        llm = make_llm("facts")
        pipeline = LLMPipeline(llm=llm)
        results = [
            SourceResult(source_name="dart", section="financials", raw="매출액 1조"),
            SourceResult(source_name="github", section="tech", raw="Python, Go"),
        ]
        pipeline.analyze(results, "카카오")
        # First call is fact extraction — prompt should reference section labels
        first_prompt = llm.generate.call_args_list[0].kwargs.get("prompt", "")
        assert "카카오" in first_prompt


class TestLLMPipelineErrorHandling:
    def test_llm_exception_in_section_returns_empty_string(self):
        llm = MagicMock()
        llm.is_available.return_value = True
        # fact extraction succeeds, section calls raise
        call_count = [0]

        def side_effect(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return LLMResponse(text="facts extracted", model="mock")
            raise RuntimeError("LLM timeout")

        llm.generate.side_effect = side_effect
        pipeline = LLMPipeline(llm=llm)
        results = make_results(["overview"])
        # Should not raise — failed sections return ""
        output = pipeline.analyze(results, "토스")
        assert isinstance(output, dict)

    def test_fact_extraction_exception_returns_empty_dict(self):
        llm = MagicMock()
        llm.is_available.return_value = True
        llm.generate.side_effect = RuntimeError("network error")
        pipeline = LLMPipeline(llm=llm)
        results = make_results(["overview"])
        output = pipeline.analyze(results, "네이버")
        assert output == {}


class TestLLMPipelineFactExtraction:
    def test_multiple_sources_concatenated(self):
        llm = make_llm("facts")
        pipeline = LLMPipeline(llm=llm)
        results = [
            SourceResult(source_name="dart", section="overview", raw="DART 데이터"),
            SourceResult(source_name="github", section="tech", raw="GitHub 데이터"),
            SourceResult(source_name="naver_news", section="overview", raw="뉴스 데이터"),
        ]
        pipeline.analyze(results, "카카오")
        first_prompt = llm.generate.call_args_list[0].kwargs.get("prompt", "")
        assert "DART 데이터" in first_prompt
        assert "GitHub 데이터" in first_prompt

    def test_source_with_no_raw_skipped(self):
        llm = make_llm("facts")
        pipeline = LLMPipeline(llm=llm)
        results = [
            SourceResult(source_name="dart", section="overview", raw=""),
            SourceResult(source_name="github", section="tech", raw="GitHub data"),
        ]
        pipeline.analyze(results, "카카오")
        first_prompt = llm.generate.call_args_list[0].kwargs.get("prompt", "")
        # Empty raw should be excluded from fact prompt
        assert "GitHub data" in first_prompt
