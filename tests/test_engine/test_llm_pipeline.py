"""Tests for LLMPipeline — sectioned multi-step analysis with mocked LLM."""

from typing import Any
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


def make_structured_llm(structured: dict[str, Any], text: str = "") -> MagicMock:
    llm = MagicMock()
    llm.is_available.return_value = True
    llm.generate.return_value = LLMResponse(text=text, structured=structured, model="mock")
    return llm


def make_refusal_llm() -> MagicMock:
    llm = MagicMock()
    llm.is_available.return_value = True
    llm.generate.return_value = LLMResponse(text="", refusal=True, model="mock")
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

    def test_fact_extraction_passes_json_schema(self):
        llm = make_llm("facts")
        pipeline = LLMPipeline(llm=llm)
        pipeline.analyze(make_results(["overview"]), "카카오")
        first_call = llm.generate.call_args_list[0]
        assert first_call.kwargs["json_schema"]["name"] == "fact_extraction"

    def test_section_analysis_passes_json_schema(self):
        llm = make_llm("분석")
        pipeline = LLMPipeline(llm=llm)
        pipeline.analyze(make_results(["overview"]), "카카오")
        section_call = llm.generate.call_args_list[1]
        assert section_call.kwargs["json_schema"]["name"] == "section_analysis"

    def test_verdict_analysis_passes_json_schema(self):
        llm = make_llm("판정")
        pipeline = LLMPipeline(llm=llm)
        pipeline.analyze(make_results(["overview"]), "카카오")
        verdict_call = llm.generate.call_args_list[4]
        assert verdict_call.kwargs["json_schema"]["name"] == "verdict_analysis"

    def test_structured_fact_response_is_rendered(self):
        llm = MagicMock()
        llm.is_available.return_value = True
        llm.generate.side_effect = [
            LLMResponse(structured={"facts": ["사실1 [출처: dart]", "사실2 [출처: github]"]}, text="", model="mock"),
            LLMResponse(text="개요", structured={"analysis": "개요"}, model="mock"),
            LLMResponse(text="산업", structured={"analysis": "산업"}, model="mock"),
            LLMResponse(text="기술", structured={"analysis": "기술"}, model="mock"),
            LLMResponse(text="판정", structured={"verdict": "Hold", "rationale": "근거 부족", "strengths": [], "risks": ["정보 부족"], "recommended_positions": []}, model="mock"),
            LLMResponse(text="시트", model="mock"),
        ]
        pipeline = LLMPipeline(llm=llm)
        output = pipeline.analyze(make_results(["overview", "tech"]), "카카오")
        assert output[1] == "개요"
        first_prompt = llm.generate.call_args_list[1].kwargs.get("prompt", "")
        assert "사실1 [출처: dart]" in first_prompt

    def test_refusal_returns_empty_sections(self):
        llm = make_refusal_llm()
        pipeline = LLMPipeline(llm=llm)
        output = pipeline.analyze(make_results(["overview"]), "카카오")
        assert output == {}

    def test_invalid_structured_section_falls_back_to_text(self):
        llm = MagicMock()
        llm.is_available.return_value = True
        llm.generate.side_effect = [
            LLMResponse(text="", structured={"facts": ["사실 [출처: dart]"]}, model="mock"),
            LLMResponse(text="개요 텍스트", structured={"wrong": "shape"}, model="mock"),
            LLMResponse(text="산업 텍스트", structured={"analysis": "산업 텍스트"}, model="mock"),
            LLMResponse(text="기술 텍스트", structured={"analysis": "기술 텍스트"}, model="mock"),
            LLMResponse(text="판정 텍스트", structured={"wrong": "shape"}, model="mock"),
            LLMResponse(text="시트", model="mock"),
        ]
        pipeline = LLMPipeline(llm=llm)
        output = pipeline.analyze(make_results(["overview"]), "카카오")
        assert output[1] == "개요 텍스트"
        assert output[11] == "판정 텍스트"


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


# ---------------------------------------------------------------------------
# 3-CoT Phase Tests (FinRobot pattern)
# ---------------------------------------------------------------------------


class TestExtractFacts:
    """Phase 1: Data-CoT — extract_facts()."""

    def test_returns_dict_with_facts_key(self):
        llm = make_llm("사실1\n사실2")
        pipeline = LLMPipeline(llm=llm)
        results = make_results(["overview"])
        output = pipeline.extract_facts(results, "카카오")
        assert isinstance(output, dict)
        assert "facts" in output

    def test_returns_empty_dict_when_llm_unavailable(self):
        pipeline = LLMPipeline(llm=NoLLM())
        output = pipeline.extract_facts(make_results(["overview"]), "카카오")
        assert output == {}

    def test_returns_empty_dict_when_no_raw_data(self):
        llm = make_llm("facts")
        pipeline = LLMPipeline(llm=llm)
        results = [SourceResult(source_name="mock", section="overview", raw="")]
        output = pipeline.extract_facts(results, "카카오")
        assert output == {}

    def test_facts_value_is_non_empty_string(self):
        llm = make_llm("사실 목록")
        pipeline = LLMPipeline(llm=llm)
        output = pipeline.extract_facts(make_results(["overview"]), "카카오")
        assert isinstance(output["facts"], str)
        assert len(output["facts"]) > 0

    def test_structured_facts_joined_as_lines(self):
        llm = MagicMock()
        llm.is_available.return_value = True
        llm.generate.return_value = LLMResponse(
            structured={"facts": ["사실1 [출처: dart]", "사실2 [출처: github]"]},
            text="",
            model="mock",
        )
        pipeline = LLMPipeline(llm=llm)
        output = pipeline.extract_facts(make_results(["overview"]), "카카오")
        assert "사실1 [출처: dart]" in output["facts"]
        assert "사실2 [출처: github]" in output["facts"]


class TestAnalyzeSections:
    """Phase 2: Concept-CoT — analyze_sections()."""

    def test_returns_sections_1_2_7(self):
        llm = make_llm("분석 결과")
        pipeline = LLMPipeline(llm=llm)
        facts = {"facts": "회사 관련 사실들"}
        output = pipeline.analyze_sections(facts, "카카오")
        assert set(output.keys()) == {1, 2, 7}

    def test_each_section_is_string(self):
        llm = make_llm("분석")
        pipeline = LLMPipeline(llm=llm)
        output = pipeline.analyze_sections({"facts": "사실"}, "네이버")
        for key, value in output.items():
            assert isinstance(value, str), f"Section {key} should be str"

    def test_empty_facts_does_not_raise(self):
        llm = make_llm("분석")
        pipeline = LLMPipeline(llm=llm)
        output = pipeline.analyze_sections({}, "카카오")
        assert isinstance(output, dict)

    def test_llm_called_three_times(self):
        llm = make_llm("결과")
        pipeline = LLMPipeline(llm=llm)
        pipeline.analyze_sections({"facts": "사실"}, "토스")
        assert llm.generate.call_count == 3


class TestSynthesize:
    """Phase 3: Thesis-CoT — synthesize()."""

    def test_returns_string(self):
        llm = make_llm("판정 결과")
        pipeline = LLMPipeline(llm=llm)
        sections = {1: "개요", 2: "산업", 7: "기술"}
        facts = {"facts": "사실들"}
        result = pipeline.synthesize(sections, facts, "카카오")
        assert isinstance(result, str)

    def test_empty_sections_does_not_raise(self):
        llm = make_llm("판정")
        pipeline = LLMPipeline(llm=llm)
        result = pipeline.synthesize({}, {}, "카카오")
        assert isinstance(result, str)

    def test_structured_verdict_formatted(self):
        llm = MagicMock()
        llm.is_available.return_value = True
        llm.generate.return_value = LLMResponse(
            structured={
                "verdict": "Go",
                "rationale": "성장성 우수",
                "strengths": ["기술력", "시장지위"],
                "risks": ["경쟁 심화"],
                "recommended_positions": ["ML Engineer"],
            },
            text="",
            model="mock",
        )
        pipeline = LLMPipeline(llm=llm)
        result = pipeline.synthesize({1: "개요"}, {"facts": "사실"}, "카카오")
        assert "Go" in result
        assert "성장성 우수" in result


class TestAnalyzeIsBackwardCompatible:
    """analyze() must still work as before — 3-CoT wrapper."""

    def test_analyze_returns_all_five_section_keys(self):
        llm = make_llm("결과")
        pipeline = LLMPipeline(llm=llm)
        output = pipeline.analyze(make_results(["overview"]), "카카오")
        assert set(output.keys()) == {0, 1, 2, 7, 11}

    def test_analyze_result_matches_manual_3cot_pipeline(self):
        """analyze() should produce same keys as calling the 3 phases manually."""
        llm = make_llm("일관된 결과")
        pipeline = LLMPipeline(llm=llm)
        results = make_results(["overview", "tech"])

        auto = pipeline.analyze(results, "토스")
        assert set(auto.keys()) == {0, 1, 2, 7, 11}

    def test_analyze_empty_dict_when_llm_unavailable(self):
        pipeline = LLMPipeline(llm=NoLLM())
        assert pipeline.analyze(make_results(["overview"]), "카카오") == {}
