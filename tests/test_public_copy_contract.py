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
            assert "정적 스냅샷" in text or "static snapshot" in text or "advisory" in text or "권고용" in text, path

    def test_public_entry_points_position_hirekit_as_career_intelligence(self):
        assert "Career Intelligence Terminal" in read("README.md")
        assert "Career Intelligence" in read("docs/index.html")
        assert "Career Intelligence Terminal" in read("docs/ko.html")
        assert "Career Intelligence Terminal" in read("docs/en.html")

    def test_public_pages_have_war_room_section_contract(self):
        target_pages = ["docs/index.html", "docs/demo.html", "docs/tools.html", "docs/ko.html", "docs/en.html"]
        required_testids = [
            'data-testid="warroom-hero"',
            'data-testid="evidence-summary"',
            'data-testid="role-expectations"',
            'data-testid="real-work-stack"',
            'data-testid="org-health"',
            'data-testid="compensation-growth"',
            'data-testid="strategy-verdict"',
            'data-testid="strategy-next-actions"',
        ]

        for path in target_pages:
            text = read(path)
            for testid in required_testids:
                assert testid in text, f"{path} is missing {testid}"

    def test_public_copy_rejects_private_runtime_claims(self):
        forbidden_keywords = [
            "auto-apply",
            "자동 지원",
            "workspace",
            "워크스페이스",
            "account",
            "계정",
            "login",
            "로그인",
        ]
        for path in ["README.md", "docs/index.html", "docs/ko.html", "docs/en.html"]:
            text = read(path).lower()
            for keyword in forbidden_keywords:
                # We allow mentions of "no login" or "no workspace" or "login-free"
                if keyword in text:
                    # Context check: allow if preceded by "no", "without", or "not"
                    # This is a simple heuristic for the boundary ADR enforcement
                    idx = text.find(keyword)
                    context = text[max(0, idx - 20) : idx]
                    if not any(neg in context for neg in ["no ", "not ", "without ", "free", "정적", "스냅샷"]):
                        assert False, f"{path} contains forbidden private-runtime claim: '{keyword}'"
