"""HireKit MCP Server — Claude Code 네이티브 통합.

stdio JSON-RPC 2.0 transport. 외부 mcp 패키지 불필요.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

TOOLS: list[dict[str, Any]] = [
    {
        "name": "analyze_company",
        "description": "기업을 분석하여 5차원 스코어카드와 심층 리포트를 생성합니다 (14개 데이터 소스)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "company": {"type": "string", "description": "기업명 (예: 카카오, 네이버)"},
                "region": {"type": "string", "default": "kr"},
            },
            "required": ["company"],
        },
    },
    {
        "name": "match_jd",
        "description": "JD 텍스트와 프로필을 매칭하여 적합도, 스킬 갭, 접근 전략을 분석합니다",
        "inputSchema": {
            "type": "object",
            "properties": {
                "jd_text": {"type": "string", "description": "채용공고 텍스트"},
                "skills": {"type": "string", "description": "보유 기술 (쉼표 구분)"},
            },
            "required": ["jd_text"],
        },
    },
    {
        "name": "prepare_interview",
        "description": "기업에 맞는 면접 질문과 STAR 가이드를 생성합니다 (200+ 질문 뱅크)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "company": {"type": "string"},
                "role": {"type": "string", "description": "지원 직군 (backend, frontend, pm 등)"},
            },
            "required": ["company"],
        },
    },
    {
        "name": "compare_companies",
        "description": "2-5개 기업을 7차원으로 비교합니다 (성장/보상/문화/기술/브랜드/WLB/원격)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "companies": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "비교할 기업 목록",
                },
            },
            "required": ["companies"],
        },
    },
    {
        "name": "career_strategy",
        "description": "목표 기업에 맞는 커리어 전략을 분석합니다 (적합도/스킬갭/접근전략)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "목표 기업"},
                "current": {"type": "string", "description": "현재 재직 회사"},
                "role": {"type": "string"},
                "experience": {"type": "integer"},
                "skills": {"type": "string", "description": "보유 기술 (쉼표 구분)"},
            },
            "required": ["target"],
        },
    },
]

# ---------------------------------------------------------------------------
# Tool call handlers (sync — wrapped with asyncio.to_thread by caller)
# ---------------------------------------------------------------------------


def _call_analyze_company(params: dict[str, Any]) -> dict[str, Any]:
    from hirekit.core.config import load_config
    from hirekit.engine.company_analyzer import CompanyAnalyzer

    company = params["company"]
    region = params.get("region", "kr")
    config = load_config()
    analyzer = CompanyAnalyzer(config=config, use_llm=False)
    report = analyzer.analyze(company=company, region=region, tier=2)
    return {
        "company": report.company,
        "region": report.region,
        "scorecard": report.to_dict().get("scorecard", {}),
        "sections": list(report.sections.keys()),
        "source_count": len(report.source_results),
        "markdown_preview": report.to_markdown()[:2000],
    }


def _call_match_jd(params: dict[str, Any]) -> dict[str, Any]:
    from hirekit.core.config import load_config
    from hirekit.engine.jd_matcher import JDMatcher
    from hirekit.llm.base import NoLLM

    jd_text = params["jd_text"]
    skills_raw = params.get("skills", "")
    skills = [s.strip() for s in skills_raw.split(",") if s.strip()] if skills_raw else []

    config = load_config()
    matcher = JDMatcher(llm=NoLLM())
    profile: dict[str, Any] = {}
    if skills:
        profile["skills"] = skills
    analysis = matcher.analyze(jd_source=jd_text, profile=profile)
    return {
        "title": analysis.title,
        "company": analysis.company,
        "match_score": analysis.match_score,
        "match_grade": analysis.match_grade,
        "strengths": analysis.strengths[:5],
        "gaps": analysis.gaps[:5],
        "approach": getattr(analysis, "approach_strategy", ""),
    }


def _call_prepare_interview(params: dict[str, Any]) -> dict[str, Any]:
    from hirekit.engine.interview_prep import InterviewPrep
    from hirekit.llm.base import NoLLM

    company = params["company"]
    role = params.get("role", "")
    prep = InterviewPrep(llm=NoLLM())
    guide = prep.prepare(company=company, position=role, profile={})
    return {
        "company": company,
        "role": role,
        "common_questions": guide.common_questions[:5],
        "technical_questions": guide.technical_questions[:5],
        "behavioral_questions": guide.behavioral_questions[:5],
        "reverse_questions": guide.reverse_questions[:3],
        "total_questions": (
            len(guide.common_questions)
            + len(guide.technical_questions)
            + len(guide.behavioral_questions)
        ),
    }


def _call_compare_companies(params: dict[str, Any]) -> dict[str, Any]:
    from hirekit.engine.company_comparator import CompanyComparator

    companies: list[str] = params["companies"]
    comparator = CompanyComparator()
    result = comparator.compare(companies=companies)
    return {
        "companies": result.companies,
        "winner": result.winner,
        "overall_scores": result.overall_scores,
        "winner_by_dimension": result.winner_by_dimension,
        "recommendation": result.overall_recommendation,
        "dimensions": result.dimensions,
    }


def _call_career_strategy(params: dict[str, Any]) -> dict[str, Any]:
    from hirekit.engine.career_strategy import CareerProfile, CareerStrategyEngine

    target = params["target"]
    skills_raw = params.get("skills", "")
    skills = [s.strip() for s in skills_raw.split(",") if s.strip()] if skills_raw else []
    profile = CareerProfile(
        target_company=target,
        current_company=params.get("current"),
        years_of_experience=params.get("experience", 0),
        target_role=params.get("role", ""),
        skills=skills,
    )
    engine = CareerStrategyEngine()
    strategy = engine.analyze(profile=profile)
    return {
        "target": target,
        "fit_score": strategy.fit_score,
        "approach_strategy": strategy.approach_strategy,
        "resume_focus": strategy.resume_focus[:5],
        "interview_prep": strategy.interview_prep[:5],
        "timeline": strategy.timeline,
        "alternative_companies": strategy.alternative_companies[:3],
        "skill_gaps": [
            {"skill": g.skill, "importance": g.importance, "suggestion": g.learning_suggestion}
            for g in strategy.gap_analysis[:5]
        ],
    }


_TOOL_HANDLERS = {
    "analyze_company": _call_analyze_company,
    "match_jd": _call_match_jd,
    "prepare_interview": _call_prepare_interview,
    "compare_companies": _call_compare_companies,
    "career_strategy": _call_career_strategy,
}

# ---------------------------------------------------------------------------
# JSON-RPC request handling
# ---------------------------------------------------------------------------


def _make_response(request_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _make_error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }


async def _call_tool(name: str, arguments: dict[str, Any]) -> Any:
    handler = _TOOL_HANDLERS.get(name)
    if handler is None:
        raise ValueError(f"Unknown tool: {name}")
    return await asyncio.to_thread(handler, arguments)


async def handle_request(request: dict[str, Any]) -> dict[str, Any] | None:
    """Handle a single JSON-RPC request. Returns None for notifications."""
    req_id = request.get("id")
    method = request.get("method", "")

    try:
        if method == "initialize":
            return _make_response(
                req_id,
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "hirekit", "version": "0.1.0"},
                },
            )

        if method == "initialized":
            # notification — no response
            return None

        if method == "tools/list":
            return _make_response(req_id, {"tools": TOOLS})

        if method == "tools/call":
            params = request.get("params", {})
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            result = await _call_tool(tool_name, arguments)
            return _make_response(
                req_id,
                {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, ensure_ascii=False, indent=2),
                        }
                    ]
                },
            )

        if method == "ping":
            return _make_response(req_id, {})

        return _make_error(req_id, -32601, f"Method not found: {method}")

    except Exception as exc:  # noqa: BLE001
        logger.exception("Error handling request")
        return _make_error(req_id, -32603, str(exc))


# ---------------------------------------------------------------------------
# Main stdio loop
# ---------------------------------------------------------------------------


async def run_server() -> None:
    """Read newline-delimited JSON-RPC from stdin, write responses to stdout."""
    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)

    stdout = sys.stdout.buffer  # write bytes directly

    while True:
        try:
            line = await reader.readline()
        except Exception:
            break
        if not line:
            break
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError as exc:
            response = _make_error(None, -32700, f"Parse error: {exc}")
            stdout.write((json.dumps(response, ensure_ascii=False) + "\n").encode())
            stdout.flush()
            continue

        response = await handle_request(request)
        if response is not None:
            stdout.write((json.dumps(response, ensure_ascii=False) + "\n").encode())
            stdout.flush()


def main() -> None:
    """Entry point for `hirekit mcp-serve`."""
    logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
