from __future__ import annotations

import json

from hirekit.sources.kr.pension import PensionSource


class TestPensionSource:
    def test_collect_includes_employment_growth_reality(self, monkeypatch, tmp_path):
        payload = {
            "카카오": {
                "pension_members": 1234,
                "pension_date": "2026-03-01",
                "pension_source": "국민연금",
            }
        }
        data_path = tmp_path / "pension.json"
        data_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

        source = PensionSource()
        monkeypatch.setattr("hirekit.sources.kr.pension._DATA_PATH", data_path)

        results = source.collect("카카오")

        assert len(results) == 1
        result = results[0]
        assert result.source_authority == "official"
        assert result.freshness_policy == "core_company_fact"
        assert result.data["employment_growth_reality"]["pension_members"] == 1234
