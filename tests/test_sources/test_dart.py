"""Tests for DartSource — mocked HTTP, no real API calls."""

from unittest.mock import MagicMock, patch
import xml.etree.ElementTree as ET

import pytest

from hirekit.sources.kr.dart import DartSource, KNOWN_CORPS


class TestDartSourceAvailability:
    def test_unavailable_without_api_key(self, monkeypatch):
        monkeypatch.delenv("DART_API_KEY", raising=False)
        source = DartSource()
        assert source.is_available() is False

    def test_available_with_api_key(self, monkeypatch):
        monkeypatch.setenv("DART_API_KEY", "test_key_123")
        source = DartSource()
        assert source.is_available() is True

    def test_collect_returns_empty_without_api_key(self, monkeypatch):
        monkeypatch.delenv("DART_API_KEY", raising=False)
        source = DartSource()
        assert source.collect("카카오") == []


class TestDartSourceCorpCodeResolution:
    def test_known_company_resolved_from_map(self, monkeypatch):
        monkeypatch.setenv("DART_API_KEY", "key")
        source = DartSource()
        # 카카오 is in KNOWN_CORPS
        code = source._resolve_corp_code("카카오", "key")
        assert code == KNOWN_CORPS["카카오"]

    def test_partial_name_match_in_known_corps(self, monkeypatch):
        monkeypatch.setenv("DART_API_KEY", "key")
        source = DartSource()
        # "토스뱅크" should match known entry
        code = source._resolve_corp_code("토스뱅크", "key")
        assert code is not None

    def test_unknown_company_falls_back_to_xml_search(self, monkeypatch, tmp_path):
        monkeypatch.setenv("DART_API_KEY", "key")
        source = DartSource()

        with patch.object(source, "_search_corp_xml", return_value="99999999") as mock_xml:
            code = source._resolve_corp_code("알수없는회사XYZ", "key")
            mock_xml.assert_called_once()
            assert code == "99999999"


class TestDartSourceParseCorpXml:
    def _build_xml(self, entries: list[dict]) -> bytes:
        root = ET.Element("result")
        for e in entries:
            item = ET.SubElement(root, "list")
            for k, v in e.items():
                child = ET.SubElement(item, k)
                child.text = v
        return ET.tostring(root, encoding="utf-8", xml_declaration=True)

    def test_exact_match_returned(self, tmp_path):
        xml_data = self._build_xml([
            {"corp_name": "카카오", "corp_code": "00258801", "stock_code": "035720"},
        ])
        xml_path = tmp_path / "corps.xml"
        xml_path.write_bytes(xml_data)

        source = DartSource()
        code = source._parse_corp_xml(xml_path, "카카오")
        assert code == "00258801"

    def test_listed_company_preferred_over_unlisted(self, tmp_path):
        xml_data = self._build_xml([
            {"corp_name": "카카오", "corp_code": "UNLISTED", "stock_code": ""},
            {"corp_name": "카카오", "corp_code": "LISTED", "stock_code": "035720"},
        ])
        xml_path = tmp_path / "corps.xml"
        xml_path.write_bytes(xml_data)

        source = DartSource()
        code = source._parse_corp_xml(xml_path, "카카오")
        assert code == "LISTED"

    def test_no_match_returns_none(self, tmp_path):
        xml_data = self._build_xml([
            {"corp_name": "삼성전자", "corp_code": "00126380", "stock_code": "005930"},
        ])
        xml_path = tmp_path / "corps.xml"
        xml_path.write_bytes(xml_data)

        source = DartSource()
        result = source._parse_corp_xml(xml_path, "존재하지않는회사")
        assert result is None

    def test_partial_name_match(self, tmp_path):
        xml_data = self._build_xml([
            {"corp_name": "카카오뱅크", "corp_code": "01456825", "stock_code": "323410"},
        ])
        xml_path = tmp_path / "corps.xml"
        xml_path.write_bytes(xml_data)

        source = DartSource()
        code = source._parse_corp_xml(xml_path, "카카오뱅크")
        assert code == "01456825"


class TestDartSourceFormatHelpers:
    def test_format_overview_includes_all_fields(self):
        data = {
            "company_name": "카카오",
            "company_name_eng": "Kakao",
            "ceo": "홍은택",
            "established": "20061003",
            "address": "제주",
            "homepage": "https://kakao.com",
            "stock_code": "035720",
            "industry_code": "63999",
        }
        text = DartSource._format_overview(data)
        assert "카카오" in text
        assert "홍은택" in text
        assert "035720" in text

    def test_format_employees_includes_headcount(self):
        emp_list = [
            {
                "position": "사원",
                "gender": "남",
                "headcount": "1000",
                "avg_tenure_year": "3.5",
                "total_salary": "5000",
            }
        ]
        text = DartSource._format_employees(emp_list)
        assert "1000" in text
        assert "3.5" in text

    def test_format_financials_includes_accounts(self):
        fin_list = [
            {
                "account": "매출액",
                "current_amount": "3000000000000",
                "previous_amount": "2500000000000",
                "two_years_ago": "2000000000000",
            }
        ]
        text = DartSource._format_financials(fin_list)
        assert "매출액" in text
        assert "3000000000000" in text


class TestDartSourceCollect:
    def test_collect_with_mocked_api_returns_results(self, monkeypatch, tmp_path):
        monkeypatch.setenv("DART_API_KEY", "testkey")
        source = DartSource()

        overview_data = {
            "status": "000",
            "corp_name": "카카오",
            "corp_name_eng": "Kakao",
            "ceo_nm": "홍은택",
            "est_dt": "20061003",
            "adres": "제주",
            "hm_url": "https://kakao.com",
            "stock_code": "035720",
            "corp_cls": "Y",
            "induty_code": "63999",
            "ir_url": "",
            "stock_name": "카카오",
        }

        emp_data = {
            "status": "000",
            "list": [
                {
                    "fo_bbm": "사원", "sexdstn": "남", "rgllbr_co": "1000",
                    "cnttk_co": "50", "sm": "1050",
                    "avrg_cnwk_sdytrn": "3.5", "jan_salary_am": "5000",
                    "sm_a": "50000",
                }
            ],
        }

        fin_data = {
            "status": "000",
            "list": [
                {
                    "account_nm": "매출액",
                    "thstrm_amount": "3000000000000",
                    "frmtrm_amount": "2500000000000",
                    "bfefrmtrm_amount": "2000000000000",
                }
            ],
        }

        mock_responses = [overview_data, emp_data, fin_data]
        call_count = [0]

        def mock_get(*args, **kwargs):
            resp = MagicMock()
            resp.status_code = 200
            resp.json.return_value = mock_responses[call_count[0] % len(mock_responses)]
            call_count[0] += 1
            return resp

        with patch("httpx.get", side_effect=mock_get):
            results = source.collect("카카오", corp_code="00258801")

        assert len(results) >= 1
        source_names = [r.source_name for r in results]
        assert all(n == "dart" for n in source_names)
        sections = [r.section for r in results]
        assert "overview" in sections

    def test_collect_returns_empty_on_api_error(self, monkeypatch):
        monkeypatch.setenv("DART_API_KEY", "testkey")
        source = DartSource()

        with patch.object(source, "_resolve_corp_code", return_value=None):
            results = source.collect("알수없는회사")
        assert results == []
