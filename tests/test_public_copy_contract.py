from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).parent.parent


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


class TestPublicCopyContract:
    def test_readme_and_landing_use_updated_company_count(self):
        assert "79개" in read("README.md")
        assert "79" in read("docs/index.html")

    def test_public_entry_points_explain_snapshot_or_advisory_limit(self):
        for path in ["README.md", "docs/index.html", "docs/ko.html", "docs/en.html"]:
            text = read(path)
            assert (
                "정적 스냅샷" in text
                or "static snapshot" in text
                or "advisory" in text
                or "권고용" in text
            ), path

    def test_public_entry_points_position_hirekit_as_career_intelligence(self):
        assert "Career Intelligence Terminal" in read("README.md")
        assert "Career Intelligence" in read("docs/index.html")
        assert "Career Intelligence Terminal" in read("docs/ko.html")
        assert "Career Intelligence Terminal" in read("docs/en.html")
