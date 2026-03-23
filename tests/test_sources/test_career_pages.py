"""Tests for career_pages collector — mocked HTTP, no real network calls."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from hirekit.sources.kr.career_pages import (
    GREENHOUSE_BOARDS,
    GREETING_SLUGS,
    NAVER_COMPANIES,
    CareerPagesSource,
    JobPosting,
    JobPostingCollector,
)


# ---------------------------------------------------------------------------
# JobPosting dataclass
# ---------------------------------------------------------------------------

class TestJobPostingDataclass:
    def test_required_fields(self):
        p = JobPosting(title="백엔드 개발자", company="쿠팡", url="https://example.com")
        assert p.title == "백엔드 개발자"
        assert p.company == "쿠팡"
        assert p.url == "https://example.com"

    def test_optional_fields_default_to_empty(self):
        p = JobPosting(title="t", company="c", url="u")
        assert p.location == ""
        assert p.department == ""
        assert p.employment_type == ""
        assert p.posted_at == ""
        assert p.description_snippet == ""

    def test_all_fields_settable(self):
        p = JobPosting(
            title="프론트엔드",
            company="당근",
            url="https://boards.greenhouse.io/daangn/1",
            location="서울",
            department="플랫폼",
            employment_type="정규직",
            posted_at="2024-01-15",
            description_snippet="React, TypeScript...",
        )
        assert p.location == "서울"
        assert p.department == "플랫폼"
        assert p.employment_type == "정규직"
        assert p.posted_at == "2024-01-15"


# ---------------------------------------------------------------------------
# Constants / mappings
# ---------------------------------------------------------------------------

class TestMappings:
    def test_greenhouse_boards_contains_known_companies(self):
        assert "쿠팡" in GREENHOUSE_BOARDS
        assert "당근" in GREENHOUSE_BOARDS
        assert "크래프톤" in GREENHOUSE_BOARDS

    def test_greenhouse_board_values_are_strings(self):
        for company, board in GREENHOUSE_BOARDS.items():
            assert isinstance(board, str), f"{company} board token should be str"
            assert board  # non-empty

    def test_greeting_slugs_contains_known_companies(self):
        assert "카카오페이" in GREETING_SLUGS
        assert "컬리" in GREETING_SLUGS
        assert "리디" in GREETING_SLUGS

    def test_naver_companies_is_frozenset(self):
        assert isinstance(NAVER_COMPANIES, frozenset)
        assert "네이버" in NAVER_COMPANIES


# ---------------------------------------------------------------------------
# collect_all routing
# ---------------------------------------------------------------------------

class TestCollectAllRouting:
    def test_routes_greenhouse_company(self):
        collector = JobPostingCollector()
        with patch.object(collector, "collect_greenhouse", return_value=[]) as mock_gh:
            collector.collect_all("쿠팡")
            mock_gh.assert_called_once_with("쿠팡")

    def test_routes_greeting_company(self):
        collector = JobPostingCollector()
        with patch.object(collector, "collect_greeting", return_value=[]) as mock_gr:
            collector.collect_all("카카오페이")
            mock_gr.assert_called_once_with("카카오페이")

    def test_routes_naver_company(self):
        collector = JobPostingCollector()
        with patch.object(collector, "collect_naver", return_value=[]) as mock_nv:
            collector.collect_all("네이버")
            mock_nv.assert_called_once()

    def test_routes_naver_subsidiary(self):
        collector = JobPostingCollector()
        with patch.object(collector, "collect_naver", return_value=[]) as mock_nv:
            collector.collect_all("네이버클라우드")
            mock_nv.assert_called_once()

    def test_unknown_company_returns_empty(self):
        collector = JobPostingCollector()
        result = collector.collect_all("알수없는회사XYZ")
        assert result == []


# ---------------------------------------------------------------------------
# collect_greenhouse — mocked HTTP
# ---------------------------------------------------------------------------

_GREENHOUSE_RESPONSE = {
    "jobs": [
        {
            "title": "백엔드 개발자",
            "absolute_url": "https://boards.greenhouse.io/coupang/jobs/1001",
            "location": {"name": "서울"},
            "departments": [{"name": "Engineering"}],
            "updated_at": "2024-03-01T00:00:00Z",
        },
        {
            "title": "데이터 엔지니어",
            "absolute_url": "https://boards.greenhouse.io/coupang/jobs/1002",
            "location": {"name": "서울"},
            "departments": [],
            "updated_at": "2024-03-02T00:00:00Z",
        },
    ]
}


class TestCollectGreenhouse:
    def _mock_client_get(self, json_data: dict):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = json_data
        return mock_resp

    def test_parses_title_and_url(self):
        collector = JobPostingCollector()
        collector.client.get = MagicMock(
            return_value=self._mock_client_get(_GREENHOUSE_RESPONSE)
        )
        postings = collector.collect_greenhouse("쿠팡")
        assert len(postings) == 2
        assert postings[0].title == "백엔드 개발자"
        assert "1001" in postings[0].url

    def test_parses_location(self):
        collector = JobPostingCollector()
        collector.client.get = MagicMock(
            return_value=self._mock_client_get(_GREENHOUSE_RESPONSE)
        )
        postings = collector.collect_greenhouse("쿠팡")
        assert postings[0].location == "서울"

    def test_parses_department_when_present(self):
        collector = JobPostingCollector()
        collector.client.get = MagicMock(
            return_value=self._mock_client_get(_GREENHOUSE_RESPONSE)
        )
        postings = collector.collect_greenhouse("쿠팡")
        assert postings[0].department == "Engineering"

    def test_empty_departments_list_yields_empty_string(self):
        collector = JobPostingCollector()
        collector.client.get = MagicMock(
            return_value=self._mock_client_get(_GREENHOUSE_RESPONSE)
        )
        postings = collector.collect_greenhouse("쿠팡")
        assert postings[1].department == ""

    def test_posted_at_truncated_to_date(self):
        collector = JobPostingCollector()
        collector.client.get = MagicMock(
            return_value=self._mock_client_get(_GREENHOUSE_RESPONSE)
        )
        postings = collector.collect_greenhouse("쿠팡")
        assert postings[0].posted_at == "2024-03-01"

    def test_company_set_correctly(self):
        collector = JobPostingCollector()
        collector.client.get = MagicMock(
            return_value=self._mock_client_get(_GREENHOUSE_RESPONSE)
        )
        postings = collector.collect_greenhouse("쿠팡")
        assert all(p.company == "쿠팡" for p in postings)

    def test_unknown_company_returns_empty_without_request(self):
        collector = JobPostingCollector()
        collector.client.get = MagicMock()
        result = collector.collect_greenhouse("알수없는회사")
        assert result == []
        collector.client.get.assert_not_called()

    def test_http_error_returns_empty(self):
        collector = JobPostingCollector()
        collector.client.get = MagicMock(side_effect=Exception("connection error"))
        result = collector.collect_greenhouse("쿠팡")
        assert result == []

    def test_empty_jobs_list(self):
        collector = JobPostingCollector()
        collector.client.get = MagicMock(
            return_value=self._mock_client_get({"jobs": []})
        )
        result = collector.collect_greenhouse("당근")
        assert result == []


# ---------------------------------------------------------------------------
# collect_naver — mocked HTTP
# ---------------------------------------------------------------------------

_NAVER_RESPONSE = {
    "list": [
        {
            "rcrtNo": "N001",
            "jobNm": "서버 개발자",
            "workLocNm": "성남",
            "deptNm": "서버개발팀",
            "enterTypeNm": "정규직",
            "rcrtEndDt": "2024-04-30",
        },
        {
            "rcrtNo": "N002",
            "jobNm": "iOS 개발자",
            "workLocNm": "성남",
            "deptNm": "모바일팀",
            "enterTypeNm": "정규직",
            "rcrtEndDt": "2024-04-30",
        },
    ]
}


class TestCollectNaver:
    def _mock_client_post(self, json_data: dict):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = json_data
        return mock_resp

    def test_parses_title(self):
        collector = JobPostingCollector()
        collector.client.post = MagicMock(
            return_value=self._mock_client_post(_NAVER_RESPONSE)
        )
        postings = collector.collect_naver()
        assert len(postings) == 2
        assert postings[0].title == "서버 개발자"

    def test_url_contains_recruit_no(self):
        collector = JobPostingCollector()
        collector.client.post = MagicMock(
            return_value=self._mock_client_post(_NAVER_RESPONSE)
        )
        postings = collector.collect_naver()
        assert "N001" in postings[0].url
        assert "recruit.navercorp.com" in postings[0].url

    def test_company_is_naver(self):
        collector = JobPostingCollector()
        collector.client.post = MagicMock(
            return_value=self._mock_client_post(_NAVER_RESPONSE)
        )
        postings = collector.collect_naver()
        assert all(p.company == "네이버" for p in postings)

    def test_http_error_returns_empty(self):
        collector = JobPostingCollector()
        collector.client.post = MagicMock(side_effect=Exception("timeout"))
        result = collector.collect_naver()
        assert result == []

    def test_empty_list_returns_empty(self):
        collector = JobPostingCollector()
        collector.client.post = MagicMock(
            return_value=self._mock_client_post({"list": []})
        )
        result = collector.collect_naver()
        assert result == []


# ---------------------------------------------------------------------------
# collect_greeting — mocked HTTP (HTML)
# ---------------------------------------------------------------------------

_GREETING_HTML = """
<html><body>
  <a href="/career/101">
    <h3 class="title">백엔드 개발자</h3>
    <span class="department">서버개발팀</span>
  </a>
  <a href="/career/102">
    <h3 class="title">프론트엔드 개발자</h3>
  </a>
  <a href="/about">About Us</a>
</body></html>
"""


class TestCollectGreeting:
    def _mock_client_get(self, text: str, status: int = 200):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.text = text
        mock_resp.status_code = status
        return mock_resp

    def test_parses_job_cards(self):
        collector = JobPostingCollector()
        collector.client.get = MagicMock(
            return_value=self._mock_client_get(_GREETING_HTML)
        )
        postings = collector.collect_greeting("카카오페이")
        titles = [p.title for p in postings]
        assert "백엔드 개발자" in titles
        assert "프론트엔드 개발자" in titles

    def test_skips_non_career_links(self):
        collector = JobPostingCollector()
        collector.client.get = MagicMock(
            return_value=self._mock_client_get(_GREETING_HTML)
        )
        postings = collector.collect_greeting("카카오페이")
        # /about should not appear
        assert all("about" not in p.url.lower() for p in postings)

    def test_parses_department(self):
        collector = JobPostingCollector()
        collector.client.get = MagicMock(
            return_value=self._mock_client_get(_GREETING_HTML)
        )
        postings = collector.collect_greeting("카카오페이")
        be = next(p for p in postings if p.title == "백엔드 개발자")
        assert be.department == "서버개발팀"

    def test_company_set_correctly(self):
        collector = JobPostingCollector()
        collector.client.get = MagicMock(
            return_value=self._mock_client_get(_GREETING_HTML)
        )
        postings = collector.collect_greeting("카카오페이")
        assert all(p.company == "카카오페이" for p in postings)

    def test_url_built_with_slug(self):
        collector = JobPostingCollector()
        collector.client.get = MagicMock(
            return_value=self._mock_client_get(_GREETING_HTML)
        )
        postings = collector.collect_greeting("카카오페이")
        assert all("kakaopay.career.greetinghr.com" in p.url for p in postings)

    def test_unknown_company_returns_empty_without_request(self):
        collector = JobPostingCollector()
        collector.client.get = MagicMock()
        result = collector.collect_greeting("알수없는회사")
        assert result == []
        collector.client.get.assert_not_called()

    def test_http_error_returns_empty(self):
        collector = JobPostingCollector()
        collector.client.get = MagicMock(side_effect=Exception("timeout"))
        result = collector.collect_greeting("컬리")
        assert result == []

    def test_deduplicates_by_url(self):
        html = """
        <html><body>
          <a href="/career/1"><h3 class="title">개발자</h3></a>
          <a href="/career/1"><h3 class="title">개발자</h3></a>
        </body></html>
        """
        collector = JobPostingCollector()
        collector.client.get = MagicMock(
            return_value=self._mock_client_get(html)
        )
        postings = collector.collect_greeting("컬리")
        assert len(postings) == 1


# ---------------------------------------------------------------------------
# CareerPagesSource (BaseSource integration)
# ---------------------------------------------------------------------------

class TestCareerPagesSource:
    def test_is_available_always_true(self):
        source = CareerPagesSource()
        assert source.is_available() is True

    def test_collect_returns_source_result(self):
        source = CareerPagesSource()
        postings = [
            JobPosting(title="백엔드 개발자", company="쿠팡", url="https://example.com/1"),
            JobPosting(title="데이터 엔지니어", company="쿠팡", url="https://example.com/2"),
        ]
        with patch(
            "hirekit.sources.kr.career_pages.JobPostingCollector.collect_all",
            return_value=postings,
        ):
            results = source.collect("쿠팡")

        assert len(results) == 1
        result = results[0]
        assert result.source_name == "career_pages"
        assert result.section == "job"
        assert result.data["total_positions"] == 2

    def test_collect_returns_empty_when_no_postings(self):
        source = CareerPagesSource()
        with patch(
            "hirekit.sources.kr.career_pages.JobPostingCollector.collect_all",
            return_value=[],
        ):
            results = source.collect("알수없는회사")
        assert results == []

    def test_result_data_contains_jobs_list(self):
        source = CareerPagesSource()
        postings = [
            JobPosting(
                title="ML 엔지니어",
                company="크래프톤",
                url="https://example.com/3",
                department="AI Lab",
                location="서울",
                posted_at="2024-03-01",
            )
        ]
        with patch(
            "hirekit.sources.kr.career_pages.JobPostingCollector.collect_all",
            return_value=postings,
        ):
            results = source.collect("크래프톤")

        jobs = results[0].data["jobs"]
        assert len(jobs) == 1
        assert jobs[0]["title"] == "ML 엔지니어"
        assert jobs[0]["department"] == "AI Lab"

    def test_result_raw_contains_title(self):
        source = CareerPagesSource()
        postings = [JobPosting(title="iOS 개발자", company="당근", url="https://x.com")]
        with patch(
            "hirekit.sources.kr.career_pages.JobPostingCollector.collect_all",
            return_value=postings,
        ):
            results = source.collect("당근")
        assert "iOS 개발자" in results[0].raw

    def test_source_name_and_region(self):
        source = CareerPagesSource()
        assert source.name == "career_pages"
        assert source.region == "kr"
        assert "job" in source.sections
