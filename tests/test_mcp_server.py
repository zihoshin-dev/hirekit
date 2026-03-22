"""Tests for HireKit MCP server (stdio JSON-RPC)."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import MagicMock, patch

import pytest

from hirekit.mcp_server import TOOLS, handle_request


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
    mock_report = MagicMock()
    mock_report.company = "카카오"
    mock_report.region = "kr"
    mock_report.source_results = []
    mock_report.sections = {1: {}, 3: {}}
    mock_report.to_dict.return_value = {
        "scorecard": {"total": 75.0, "grade": "B", "dimensions": []}
    }
    mock_report.to_markdown.return_value = "# 카카오 분석 리포트\n..."

    mock_analyzer = MagicMock()
    mock_analyzer.analyze.return_value = mock_report

    with patch(
        "hirekit.mcp_server._call_analyze_company",
        return_value={
            "company": "카카오",
            "region": "kr",
            "scorecard": {"total": 75.0, "grade": "B", "dimensions": []},
            "sections": [1, 3],
            "source_count": 0,
            "markdown_preview": "# 카카오 분석 리포트\n...",
        },
    ):
        request = {
            "jsonrpc": "2.0",
            "id": 10,
            "method": "tools/call",
            "params": {
                "name": "analyze_company",
                "arguments": {"company": "카카오", "region": "kr"},
            },
        }
        response = await handle_request(request)

    assert response is not None
    assert response["id"] == 10
    content = response["result"]["content"]
    assert len(content) == 1
    assert content[0]["type"] == "text"
    data = json.loads(content[0]["text"])
    assert data["company"] == "카카오"
    assert "scorecard" in data


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
