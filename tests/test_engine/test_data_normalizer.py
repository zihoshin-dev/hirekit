"""Tests for data_normalizer — raw source data → template-ready format."""

from hirekit.engine.data_normalizer import (
    _clean_text,
    _format_amount,
    _format_date,
    _parse_number,
    normalize_evidence_bundle,
    normalize_sections,
)


class TestFormatDate:
    def test_valid_yyyymmdd(self):
        assert _format_date("20190315") == "2019년 3월 15일"

    def test_single_digit_month_and_day(self):
        assert _format_date("20230101") == "2023년 1월 1일"

    def test_empty_string_returns_dash(self):
        assert _format_date("") == "—"

    def test_too_short_string_returned_as_is(self):
        assert _format_date("2023") == "2023"

    def test_invalid_string_returned_as_is(self):
        assert _format_date("notadate") == "notadate"

    def test_none_like_falsy_returns_dash(self):
        assert _format_date("") == "—"


class TestFormatAmount:
    def test_trillion_unit(self):
        result = _format_amount("2000000000000")
        assert result == "2.0조"

    def test_billion_unit(self):
        result = _format_amount("50000000000")
        assert result == "500억"

    def test_ten_thousand_unit(self):
        result = _format_amount("500000")
        assert result == "50만"

    def test_small_number_with_comma_separator(self):
        result = _format_amount("1,234")
        assert result == "1,234"

    def test_empty_string_returns_dash(self):
        assert _format_amount("") == "—"

    def test_non_numeric_returned_as_is(self):
        assert _format_amount("N/A") == "N/A"

    def test_negative_number_billion(self):
        result = _format_amount("-500000000000")
        assert "조" in result or "억" in result

    def test_commas_stripped_before_parsing(self):
        result = _format_amount("1,000,000,000,000")
        assert result == "1.0조"


class TestParseNumber:
    def test_plain_integer(self):
        assert _parse_number("1234") == 1234

    def test_comma_separated(self):
        assert _parse_number("1,234") == 1234

    def test_invalid_returns_zero(self):
        assert _parse_number("abc") == 0

    def test_empty_returns_zero(self):
        assert _parse_number("") == 0

    def test_none_returns_zero(self):
        assert _parse_number(None) == 0  # type: ignore[arg-type]


class TestCleanText:
    def test_removes_html_tags(self):
        assert _clean_text("<b>Hello</b> World") == "Hello World"

    def test_collapses_whitespace(self):
        assert _clean_text("  too   many   spaces  ") == "too many spaces"

    def test_strips_leading_trailing(self):
        assert _clean_text("  stripped  ") == "stripped"

    def test_nested_html_tags(self):
        result = _clean_text("<div><span>text</span></div>")
        assert result == "text"

    def test_empty_string(self):
        assert _clean_text("") == ""


class TestNormalizeSections:
    def test_non_dict_section_passed_through(self):
        result = normalize_sections({5: "plain string"})
        assert result[5] == "plain string"

    def test_unknown_section_num_shallow_copied(self):
        raw = {9: {"foo": "bar"}}
        result = normalize_sections(raw)
        assert result[9]["foo"] == "bar"

    def test_analysis_key_always_preserved(self):
        raw = {9: {"analysis": "LLM output", "foo": "bar"}}
        result = normalize_sections(raw)
        assert result[9]["analysis"] == "LLM output"

    def test_section_1_overview_normalization(self):
        raw = {
            1: {
                "company_name": "카카오",
                "ceo": "홍은택",
                "established": "20061003",
                "address": "제주특별자치도",
                "homepage": "https://kakao.com",
                "stock_code": "035720",
            }
        }
        result = normalize_sections(raw)
        s1 = result[1]
        assert s1["ceo"] == "홍은택"
        assert s1["founded"] == "2006년 10월 3일"
        assert s1["headquarters"] == "제주특별자치도"
        assert s1["homepage"] == "https://kakao.com"
        assert s1["stock_code"] == "035720"

    def test_section_1_employees_aggregated(self):
        raw = {
            1: {
                "employees": [
                    {
                        "headcount": "1,000",
                        "avg_tenure_year": "3.5",
                        "total_salary": "5000000000",
                        "position": "개발",
                        "gender": "남",
                    },
                    {
                        "headcount": "500",
                        "avg_tenure_year": "2.8",
                        "total_salary": "2000000000",
                        "position": "개발",
                        "gender": "여",
                    },
                ]
            }
        }
        result = normalize_sections(raw)
        assert result[1]["employees"] == "1,500명"
        assert result[1]["avg_tenure"] == "3.5"

    def test_section_1_empty_employees_shows_dash(self):
        raw = {1: {"employees": []}}
        result = normalize_sections(raw)
        assert result[1]["employees"] == "—"
        assert result[1]["avg_tenure"] == "—"

    def test_section_1_financials_formatted(self):
        raw = {
            1: {
                "financials": [
                    {
                        "account": "매출액",
                        "current_amount": "3000000000000",
                        "previous_amount": "2500000000000",
                        "two_years_ago": "2000000000000",
                    }
                ]
            }
        }
        result = normalize_sections(raw)
        fin = result[1]["financials"]
        assert len(fin) == 1
        assert fin[0]["account"] == "매출액"
        assert "조" in fin[0]["current"]

    def test_section_1_news_truncated_to_5_items(self):
        raw = {
            1: {"recent_news": [{"title": f"뉴스 {i}", "source": "test", "link": "http://x.com"} for i in range(10)]}
        }
        result = normalize_sections(raw)
        assert len(result[1]["recent_news"]) == 5

    def test_section_1_news_html_cleaned(self):
        raw = {1: {"recent_news": [{"title": "<b>카카오</b> 뉴스", "source": "연합", "link": "http://x.com"}]}}
        result = normalize_sections(raw)
        assert result[1]["recent_news"][0]["title"] == "카카오 뉴스"

    def test_section_4_culture_normalization(self):
        raw = {
            4: {"naver_blog": [{"title": "<b>카카오</b> 후기", "description": "좋은 회사  입니다"} for _ in range(7)]}
        }
        result = normalize_sections(raw)
        assert len(result[4]["naver_blog"]) == 5
        assert result[4]["naver_blog"][0]["title"] == "카카오 후기"
        assert result[4]["naver_blog"][0]["description"] == "좋은 회사 입니다"

    def test_section_4_exa_text_truncated_to_200(self):
        raw = {4: {"exa_culture": [{"title": "Culture", "text": "x" * 500}]}}
        result = normalize_sections(raw)
        assert len(result[4]["exa_culture"][0]["text"]) == 200

    def test_section_1_ceo_fallback_to_company_name(self):
        """When ceo key missing, falls back to company_name."""
        raw = {1: {"company_name": "토스"}}
        result = normalize_sections(raw)
        assert result[1]["ceo"] == "토스"

    def test_multiple_sections_normalized_independently(self):
        raw = {
            1: {"company_name": "네이버", "established": "19990601"},
            4: {"naver_blog": [{"title": "후기", "description": "좋아요"}]},
        }
        result = normalize_sections(raw)
        assert result[1]["founded"] == "1999년 6월 1일"
        assert len(result[4]["naver_blog"]) == 1


class TestNormalizeEvidenceBundle:
    def test_company_and_role_records_are_preserved(self):
        raw = {
            "company": {
                "entity_type": "company",
                "entity_key": "토스",
                "records": [
                    {
                        "entity_type": "company",
                        "entity_key": "토스",
                        "claim_category": "strategy",
                        "claim_key": "vision",
                        "value": "금융의 슈퍼앱",
                        "source_name": "company_website",
                        "source_authority": "company_operated",
                        "trust_label": "supporting",
                        "confidence": 0.6,
                        "collected_at": "2026-03-27T00:00:00+00:00",
                        "effective_at": "2026-03-27T00:00:00+00:00",
                        "freshness_policy": "core_company_fact",
                        "evidence_id": "company:토스:strategy:vision:company_website",
                    }
                ],
            },
            "roles": [
                {
                    "entity_type": "role",
                    "entity_key": "backend_engineer",
                    "company_key": "토스",
                    "records": [
                        {
                            "entity_type": "role",
                            "entity_key": "backend_engineer",
                            "claim_category": "stack_reality",
                            "claim_key": "stack",
                            "value": ["python", "kafka"],
                            "source_name": "job_postings",
                            "source_authority": "secondary_research",
                            "trust_label": "supporting",
                            "confidence": 0.6,
                            "collected_at": "2026-03-27T00:00:00+00:00",
                            "effective_at": "2026-03-27T00:00:00+00:00",
                            "freshness_policy": "job_posting",
                            "evidence_id": "role:backend_engineer:stack_reality:stack:job_postings",
                        }
                    ],
                }
            ],
        }

        result = normalize_evidence_bundle(raw)
        assert result["company"]["record_count"] == 1
        assert result["company"]["claim_categories"] == ["strategy"]
        assert result["roles"][0]["record_count"] == 1
        assert result["roles"][0]["claim_categories"] == ["stack_reality"]

    def test_missing_record_fields_get_safe_defaults(self):
        raw = {
            "company": {
                "entity_type": "company",
                "entity_key": "토스",
                "records": [{"claim_category": "strategy", "claim_key": "vision"}],
            },
            "roles": [],
        }

        result = normalize_evidence_bundle(raw)
        record = result["company"]["records"][0]
        assert record["source_authority"] == "secondary_research"
        assert record["trust_label"] == "unknown"
        assert record["confidence"] == 0.0
        assert record["freshness_policy"] == "supporting_signal"
