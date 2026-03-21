"""Tests for GitHubSource — mocked gh CLI, no real network calls."""

import subprocess
from unittest.mock import MagicMock, patch

from hirekit.sources.global_.github import GitHubSource


class TestGitHubSourceAvailability:
    def test_available_when_gh_auth_succeeds(self):
        source = GitHubSource()
        mock_result = MagicMock()
        mock_result.returncode = 0
        with patch("subprocess.run", return_value=mock_result):
            assert source.is_available() is True

    def test_unavailable_when_gh_auth_fails(self):
        source = GitHubSource()
        mock_result = MagicMock()
        mock_result.returncode = 1
        with patch("subprocess.run", return_value=mock_result):
            assert source.is_available() is False

    def test_unavailable_when_gh_not_installed(self):
        source = GitHubSource()
        with patch("subprocess.run", side_effect=FileNotFoundError):
            assert source.is_available() is False

    def test_unavailable_when_gh_times_out(self):
        source = GitHubSource()
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("gh", 5)):
            assert source.is_available() is False


class TestGitHubSourceFetchRepos:
    def _mock_run(self, json_lines: list[str], returncode: int = 0):
        mock = MagicMock()
        mock.returncode = returncode
        mock.stdout = "\n".join(json_lines)
        return mock

    def test_fetch_repos_parses_json_lines(self):
        source = GitHubSource()
        lines = [
            '{"name":"repo1","stargazers_count":100,"language":"Python","updated_at":"2025-01-01","fork":false,"archived":false}',
            '{"name":"repo2","stargazers_count":50,"language":"Go","updated_at":"2025-02-01","fork":false,"archived":false}',
        ]
        with patch("subprocess.run", return_value=self._mock_run(lines)):
            repos = source._fetch_repos("kakao")
        assert len(repos) == 2
        assert repos[0]["name"] == "repo1"

    def test_fetch_repos_returns_empty_on_gh_failure(self):
        source = GitHubSource()
        with patch("subprocess.run", return_value=self._mock_run([], returncode=1)):
            repos = source._fetch_repos("nonexistent-org")
        assert repos == []

    def test_fetch_repos_skips_invalid_json_lines(self):
        source = GitHubSource()
        lines = [
            '{"name":"good","stargazers_count":10,"language":"Python","updated_at":"2025-01-01","fork":false,"archived":false}',
            'not valid json',
            '{"name":"also_good","stargazers_count":5,"language":"Go","updated_at":"2025-01-01","fork":false,"archived":false}',
        ]
        with patch("subprocess.run", return_value=self._mock_run(lines)):
            repos = source._fetch_repos("kakao")
        assert len(repos) == 2


class TestGitHubSourceScoreOrg:
    def _make_repos(self, count: int, stars: int = 100, lang: str = "Python",
                    updated: str = "2025-01-01", fork: bool = False,
                    archived: bool = False) -> list[dict]:
        return [
            {
                "name": f"repo{i}",
                "stargazers_count": stars,
                "language": lang,
                "updated_at": updated,
                "fork": fork,
                "archived": archived,
            }
            for i in range(count)
        ]

    def test_score_returns_dict_with_required_keys(self):
        source = GitHubSource()
        repos = self._make_repos(5)
        result = source._score_org("kakao", repos)
        for key in ("org", "repo_count", "total_stars", "top_languages",
                    "total_score", "grade", "dimensions"):
            assert key in result, f"Missing key: {key}"

    def test_forked_and_archived_excluded(self):
        source = GitHubSource()
        repos = (
            self._make_repos(3, stars=100) +
            self._make_repos(2, fork=True) +
            self._make_repos(1, archived=True)
        )
        result = source._score_org("kakao", repos)
        assert result["repo_count"] == 3  # only non-fork, non-archived

    def test_score_bounded_0_to_100(self):
        source = GitHubSource()
        # Very large org
        repos = self._make_repos(200, stars=10000)
        result = source._score_org("kakao", repos)
        assert 0 <= result["total_score"] <= 100

    def test_empty_repos_gives_zero_score(self):
        source = GitHubSource()
        result = source._score_org("empty-org", [])
        assert result["total_score"] == 0

    def test_language_diversity_counted(self):
        source = GitHubSource()
        repos = (
            self._make_repos(2, lang="Python") +
            self._make_repos(2, lang="Go") +
            self._make_repos(2, lang="Java") +
            self._make_repos(2, lang="TypeScript") +
            self._make_repos(2, lang="Rust")
        )
        result = source._score_org("polyglot", repos)
        assert result["dimensions"]["diversity"] > 0
        assert len(result["top_languages"]) == 5

    def test_grade_assigned(self):
        source = GitHubSource()
        repos = self._make_repos(10, stars=500)
        result = source._score_org("kakao", repos)
        assert result["grade"] in ("S", "A", "B", "C", "D")


class TestGitHubSourceCollect:
    def test_collect_uses_known_org_map(self):
        source = GitHubSource()
        repos = [
            {"name": "r1", "stargazers_count": 50, "language": "Python",
             "updated_at": "2025-01-01", "fork": False, "archived": False}
        ]
        with patch.object(source, "_fetch_repos", return_value=repos) as mock_fetch:
            results = source.collect("카카오")
        # should have tried org "kakao" from DEFAULT_ORG_MAP
        mock_fetch.assert_called_once_with("kakao")
        assert len(results) == 1
        assert results[0].source_name == "github"
        assert results[0].section == "tech"

    def test_collect_falls_back_to_company_name_as_org(self):
        source = GitHubSource()
        with patch.object(source, "_fetch_repos", return_value=[]) as mock_fetch:
            source.collect("unknowncompany")
        mock_fetch.assert_called_once_with("unknowncompany")

    def test_collect_returns_empty_when_no_repos_found(self):
        source = GitHubSource()
        with patch.object(source, "_fetch_repos", return_value=[]):
            results = source.collect("カカオ")
        assert results == []

    def test_collect_result_has_url_and_raw(self):
        source = GitHubSource()
        repos = [
            {"name": "r1", "stargazers_count": 100, "language": "Go",
             "updated_at": "2025-01-01", "fork": False, "archived": False}
        ]
        with patch.object(source, "_fetch_repos", return_value=repos):
            results = source.collect("카카오")
        assert results[0].url.startswith("https://github.com/")
        assert len(results[0].raw) > 0
