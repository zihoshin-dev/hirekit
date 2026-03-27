"""Tests for HireKit MCP server (stdio JSON-RPC)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from hirekit.engine.company_analyzer import AnalysisReport
from hirekit.engine.hero_verdict import compose_hero_verdict
from hirekit.engine.scorer import Scorecard, ScoreDimension
from hirekit.mcp_server import TOOLS, handle_request
from hirekit.sources.base import SourceResult

# ---------------------------------------------------------------------------
# tools/list
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tools_list_returns_all_tools():
    request = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    response = await handle_request(request)

    assert response is not None
    assert response["id"] == 1
    result = response["result"]
    assert "tools" in result
    tool_names = {t["name"] for t in result["tools"]}
    assert tool_names == {
        "analyze_company",
        "match_jd",
        "prepare_interview",
        "compare_companies",
        "career_strategy",
    }


@pytest.mark.asyncio
async def test_tools_list_schemas_have_required_fields():
    request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    response = await handle_request(request)

    assert response is not None
    for tool in response["result"]["tools"]:
        assert "name" in tool
        assert "description" in tool
        assert "inputSchema" in tool
        schema = tool["inputSchema"]
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema


# ---------------------------------------------------------------------------
# initialize
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_initialize_returns_capabilities():
    request = {"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {}}
    response = await handle_request(request)

    assert response is not None
    assert response["id"] == 0
    result = response["result"]
    assert "capabilities" in result
    assert "serverInfo" in result
    assert result["serverInfo"]["name"] == "hirekit"


@pytest.mark.asyncio
async def test_initialized_notification_returns_none():
    request = {"jsonrpc": "2.0", "method": "initialized"}
    response = await handle_request(request)
    assert response is None


# ---------------------------------------------------------------------------
# tools/call — analyze_company (mock engine)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tools_call_analyze_company_mock():
    report = AnalysisReport(
        company="카카오",
        region="kr",
        tier=2,
        sections={
            1: {"growth_reality": {"growth": "상승"}},
            5: {"role_expectations": [{"expectations": ["Python 3년 이상 경험"]}]},
            7: {"stack_reality": {"confirmed": [{"tech": "python"}]}},
        },
        scorecard=Scorecard(
            company="카카오",
            dimensions=[
                ScoreDimension(name="job_fit", label="Job Fit", weight=0.3, score=4.5),
                ScoreDimension(name="career_leverage", label="Career Leverage", weight=0.2, score=4.0),
                ScoreDimension(name="growth", label="Growth", weight=0.2, score=4.0),
                ScoreDimension(name="compensation", label="Compensation", weight=0.15, score=3.5),
                ScoreDimension(name="culture_fit", label="Culture Fit", weight=0.15, score=3.5),
            ],
        ),
        source_results=[
            SourceResult(
                source_name="dart",
                section="overview",
                url="https://dart.fss.or.kr/",
                trust_label="verified",
            )
        ],
    )

    request = {
        "jsonrpc": "2.0",
        "id": 10,
        "method": "tools/call",
        "params": {
            "name": "analyze_company",
            "arguments": {"company": "카카오", "region": "kr"},
        },
    }

    with patch("hirekit.core.config.load_config") as mock_cfg:
        mock_cfg.return_value = MagicMock()
        with patch("hirekit.engine.company_analyzer.CompanyAnalyzer") as MockAnalyzer:
            MockAnalyzer.return_value.analyze.return_value = report
            response = await handle_request(request)

    assert response is not None
    assert response["id"] == 10
    content = response["result"]["content"]
    assert len(content) == 1
    assert content[0]["type"] == "text"
    data = json.loads(content[0]["text"])
    assert data["company"] == "카카오"
    assert "war_room" in data
    assert data["war_room"]["role_expectations"] == ["Python 3년 이상 경험"]
    assert data["war_room"]["stack_reality"]["confirmed"] == ["python"]
    assert data["war_room"]["verdict"]["label"] == compose_hero_verdict(report).label
    assert data["sources"][0]["trust_label"] == "verified"


# ---------------------------------------------------------------------------
# tools/call — unknown tool returns error
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tools_call_unknown_tool_returns_error():
    request = {
        "jsonrpc": "2.0",
        "id": 99,
        "method": "tools/call",
        "params": {"name": "nonexistent_tool", "arguments": {}},
    }
    response = await handle_request(request)

    assert response is not None
    assert "error" in response
    assert response["error"]["code"] == -32603


# ---------------------------------------------------------------------------
# unknown method returns method-not-found error
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unknown_method_returns_error():
    request = {"jsonrpc": "2.0", "id": 5, "method": "unknown/method", "params": {}}
    response = await handle_request(request)

    assert response is not None
    assert "error" in response
    assert response["error"]["code"] == -32601


# ---------------------------------------------------------------------------
# TOOLS constant sanity checks
# ---------------------------------------------------------------------------


def test_tools_constant_length():
    assert len(TOOLS) == 5


def test_all_tools_have_required_fields():
    for tool in TOOLS:
        assert "name" in tool
        assert "description" in tool
        assert "inputSchema" in tool
