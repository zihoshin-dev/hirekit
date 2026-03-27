"""Normalize raw source data into template-ready format."""

from __future__ import annotations

from typing import Any


def normalize_sections(sections: dict[int, Any]) -> dict[int, Any]:
    """Transform raw source data into clean template variables.

    Bridges the gap between SourceResult.data (raw API output)
    and report_ko.md.j2 template expectations.
    """
    normalized: dict[int, Any] = {}

    for num, data in sections.items():
        if not isinstance(data, dict):
            normalized[num] = data
            continue
        normalized[num] = _normalize_section(num, data)

    return normalized


def normalize_evidence_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    company = bundle.get("company", {})
    roles = bundle.get("roles", [])
    return {
        "company": _normalize_evidence_entity(company),
        "roles": [_normalize_evidence_entity(role) for role in roles if isinstance(role, dict)],
    }


def _normalize_evidence_entity(entity: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(entity, dict):
        return {"entity_type": "unknown", "entity_key": "", "records": []}

    records = entity.get("records", [])
    normalized_records: list[dict[str, Any]] = []
    claim_categories: set[str] = set()

    if isinstance(records, list):
        for record in records:
            if not isinstance(record, dict):
                continue
            normalized = {
                "entity_type": record.get("entity_type", entity.get("entity_type", "unknown")),
                "entity_key": record.get("entity_key", entity.get("entity_key", "")),
                "claim_category": record.get("claim_category", "unknown"),
                "claim_key": record.get("claim_key", ""),
                "value": record.get("value"),
                "source_name": record.get("source_name", ""),
                "source_authority": record.get("source_authority", "secondary_research"),
                "trust_label": record.get("trust_label", "unknown"),
                "confidence": float(record.get("confidence", 0.0)),
                "collected_at": record.get("collected_at", ""),
                "effective_at": record.get("effective_at", record.get("collected_at", "")),
                "freshness_policy": record.get("freshness_policy", "supporting_signal"),
                "evidence_id": record.get("evidence_id", ""),
            }
            claim_categories.add(str(normalized["claim_category"]))
            normalized_records.append(normalized)

    return {
        "entity_type": entity.get("entity_type", "unknown"),
        "entity_key": entity.get("entity_key", ""),
        "company_key": entity.get("company_key", entity.get("entity_key", "")),
        "records": normalized_records,
        "record_count": len(normalized_records),
        "claim_categories": sorted(claim_categories),
    }


def _normalize_section(num: int, data: dict[str, Any]) -> dict[str, Any]:
    """Normalize a single section's data."""
    result = dict(data)  # shallow copy

    if num == 1:
        result = _normalize_overview(result)
    elif num == 2:
        result = _normalize_industry(result)
    elif num == 3:
        result = _normalize_leadership(result)
    elif num == 4:
        result = _normalize_culture(result)
    elif num == 5:
        result = _normalize_role(result)
    elif num == 7:
        result = _normalize_tech(result)

    # Preserve 'analysis' key from LLM pipeline (always pass through)
    if "analysis" in data:
        result["analysis"] = data["analysis"]

    return result


def _normalize_overview(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize section 1: Company Overview."""
    result: dict[str, Any] = {}

    # Basic info
    result["ceo"] = data.get("ceo", data.get("company_name", "—"))
    result["founded"] = _format_date(data.get("established", ""))
    result["headquarters"] = data.get("address", "—")
    result["homepage"] = data.get("homepage", "")
    result["stock_code"] = data.get("stock_code", "")
    result["company_name"] = data.get("company_name", "")
    result["company_name_eng"] = data.get("company_name_eng", "")

    # Employee data
    employees = data.get("employees", [])
    if isinstance(employees, list) and employees:
        total_headcount = 0
        salary_info = []
        tenure_info = []
        for emp in employees:
            if isinstance(emp, dict):
                count = _parse_number(emp.get("headcount", "0"))
                total_headcount += count

                tenure = emp.get("avg_tenure_year", "")
                if tenure:
                    tenure_info.append(tenure)

                salary = emp.get("total_salary", "")
                if salary:
                    salary_info.append(
                        f"{emp.get('position', '')} {emp.get('gender', '')}: 정규직 {emp.get('headcount', '')}명"
                    )

        result["employees"] = f"{total_headcount:,}명" if total_headcount else "—"
        result["employee_details"] = salary_info
        result["avg_tenure"] = tenure_info[0] if tenure_info else "—"
    else:
        result["employees"] = "—"
        result["avg_tenure"] = "—"

    # Financial data
    financials = data.get("financials", [])
    if isinstance(financials, list) and financials:
        result["financials"] = [
            {
                "account": f.get("account", ""),
                "current": _format_amount(f.get("current_amount", "")),
                "previous": _format_amount(f.get("previous_amount", "")),
                "two_years_ago": _format_amount(f.get("two_years_ago", "")),
            }
            for f in financials
            if isinstance(f, dict)
        ]
    else:
        result["financials"] = []

    # News (clean up raw dicts)
    for key in ("recent_news", "google_news", "korean_credible_news", "international_news", "brave_web_results"):
        items = data.get(key, [])
        if isinstance(items, list):
            result[key] = [_clean_news_item(item) for item in items[:5] if isinstance(item, dict)]

    # Pass through string values
    for k, v in data.items():
        if k not in result and isinstance(v, str):
            result[k] = v

    return result


def _normalize_industry(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize section 2: Industry."""
    result: dict[str, Any] = {}

    # News items
    for key in ("google_news", "recent_news", "industry_news", "korean_credible_news", "international_news"):
        items = data.get(key, [])
        if isinstance(items, list):
            result[key] = [_clean_news_item(item) for item in items[:5] if isinstance(item, dict)]

    # Exa search results
    for key in ("exa_industry", "exa_market", "brave_web_results"):
        items = data.get(key, [])
        if isinstance(items, list):
            result[key] = [
                {
                    "title": _clean_text(item.get("title", "")),
                    "text": _clean_text(item.get("text", item.get("description", "")))[:300],
                    "url": item.get("url", item.get("link", "")),
                }
                for item in items[:5]
                if isinstance(item, dict)
            ]

    # Pass through scalar values and analysis
    for k, v in data.items():
        if k not in result and not isinstance(v, (dict, list)):
            result[k] = v

    return result


_AI_KEYWORDS = frozenset(["ai", "인공지능", "머신러닝", "딥러닝", "llm", "generative", "생성ai"])
_VISION_KEYWORDS = frozenset(["비전", "미션", "전략", "방향", "목표", "vision", "mission", "strategy"])
_EXPANSION_KEYWORDS = frozenset(["신사업", "확장", "글로벌", "해외", "진출", "투자", "인수", "합병"])


def _normalize_leadership(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize section 3: Leadership & Strategy.

    Extracts vision/mission/strategy summaries, AI-related signals, and
    new-business/expansion information in addition to leadership profiles.
    """
    result: dict[str, Any] = {}

    # Leadership profiles (list of dicts with name/title/bio fields)
    leaders = data.get("leaders", data.get("leadership", []))
    if isinstance(leaders, list):
        result["leaders"] = [
            {
                "name": _clean_text(str(item.get("name", ""))),
                "title": _clean_text(str(item.get("title", item.get("position", "")))),
                "bio": _clean_text(str(item.get("bio", item.get("description", ""))))[:500],
            }
            for item in leaders[:10]
            if isinstance(item, dict)
        ]
    else:
        result["leaders"] = []

    # Vision / mission / strategy — pass through structured fields directly
    for key in ("vision", "mission", "strategy", "ceo_vision", "group_strategy"):
        if key in data:
            val = data[key]
            if isinstance(val, str):
                result[key] = _clean_text(val)
            elif isinstance(val, list):
                result[key] = [_clean_text(str(item)) for item in val if item]
            else:
                result[key] = val

    # AI strategy signals — collect text snippets that mention AI keywords
    ai_signals: list[str] = []
    expansion_signals: list[str] = []

    # Scan all string fields and news items for AI/expansion keywords
    for k, v in data.items():
        if k in result:
            continue
        if isinstance(v, str):
            v_lower = v.lower()
            if any(kw in v_lower for kw in _AI_KEYWORDS):
                ai_signals.append(_clean_text(v)[:300])
            if any(kw in v_lower for kw in _EXPANSION_KEYWORDS):
                expansion_signals.append(_clean_text(v)[:300])
        elif isinstance(v, list):
            for item in v:
                if not isinstance(item, dict):
                    continue
                text = " ".join(str(item.get(f, "")) for f in ("title", "text", "description", "bio"))
                text_lower = text.lower()
                if any(kw in text_lower for kw in _AI_KEYWORDS):
                    ai_signals.append(_clean_text(text)[:300])
                if any(kw in text_lower for kw in _EXPANSION_KEYWORDS):
                    expansion_signals.append(_clean_text(text)[:300])

    # Also honour explicitly provided fields
    if "ai_strategy" in data:
        val = data["ai_strategy"]
        result["ai_strategy"] = _clean_text(str(val)) if isinstance(val, str) else val
    elif ai_signals:
        result["ai_signals"] = ai_signals[:5]

    if "expansion" in data:
        result["expansion"] = data["expansion"]
    elif expansion_signals:
        result["expansion_signals"] = expansion_signals[:3]

    # News about leadership
    for key in ("leadership_news", "google_news", "recent_news"):
        items = data.get(key, [])
        if isinstance(items, list):
            result[key] = [_clean_news_item(item) for item in items[:5] if isinstance(item, dict)]

    # Pass through scalar values not yet handled
    for k, v in data.items():
        if k not in result and not isinstance(v, (dict, list)):
            result[k] = v

    return result


def _normalize_role(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize section 5: Role / Job Description."""
    result: dict[str, Any] = {}

    # Job postings list
    jobs = data.get("jobs", data.get("job_postings", []))
    if isinstance(jobs, list):
        result["jobs"] = [
            {
                "title": _clean_text(str(item.get("title", item.get("job_title", "")))),
                "department": _clean_text(str(item.get("department", item.get("team", "")))),
                "location": _clean_text(str(item.get("location", ""))),
                "url": item.get("url", item.get("link", "")),
                "description": _clean_text(str(item.get("description", "")))[:400],
            }
            for item in jobs[:10]
            if isinstance(item, dict)
        ]
    else:
        result["jobs"] = []

    # Requirements / qualifications as clean list
    for key in ("requirements", "qualifications", "skills"):
        items = data.get(key, [])
        if isinstance(items, list):
            result[key] = [_clean_text(str(item)) for item in items[:20] if item and not isinstance(item, dict)]
        elif isinstance(items, str):
            result[key] = _clean_text(items)

    # Pass through scalar values
    for k, v in data.items():
        if k not in result and not isinstance(v, (dict, list)):
            result[k] = v

    return result


def _normalize_tech(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize section 7: AI / Tech stack."""
    result: dict[str, Any] = {}

    # GitHub data (already structured from GitHubSource)
    github = data.get("github", {})
    if isinstance(github, dict) and github:
        result["github"] = {
            "org": github.get("org", ""),
            "repo_count": github.get("repo_count", 0),
            "total_stars": github.get("total_stars", 0),
            "top_languages": github.get("top_languages", [])[:10],
            "total_score": github.get("total_score", 0),
            "grade": github.get("grade", ""),
        }

    # Tech blog posts
    for key in ("tech_blog", "tech_posts", "medium_posts", "velog_posts"):
        items = data.get(key, [])
        if isinstance(items, list):
            result[key] = [
                {
                    "title": _clean_text(str(item.get("title", ""))),
                    "url": item.get("url", item.get("link", "")),
                    "summary": _clean_text(str(item.get("summary", item.get("description", ""))))[:300],
                }
                for item in items[:5]
                if isinstance(item, dict)
            ]

    # Tech stack as a flat list of strings
    tech_stack = data.get("tech_stack", data.get("technologies", []))
    if isinstance(tech_stack, list):
        result["tech_stack"] = [_clean_text(str(t)) for t in tech_stack[:30] if t and not isinstance(t, dict)]
    elif isinstance(tech_stack, str):
        result["tech_stack"] = _clean_text(tech_stack)

    # Exa AI/tech search results
    for key in ("exa_tech", "exa_ai", "brave_tech_results"):
        items = data.get(key, [])
        if isinstance(items, list):
            result[key] = [
                {"title": _clean_text(item.get("title", "")), "text": _clean_text(item.get("text", ""))[:300]}
                for item in items[:3]
                if isinstance(item, dict)
            ]

    # Pass through scalar values
    for k, v in data.items():
        if k not in result and not isinstance(v, (dict, list)):
            result[k] = v

    return result


def _normalize_culture(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize section 4: Culture."""
    result: dict[str, Any] = {}

    # Blog/cafe reviews
    for key in ("naver_blog", "naver_cafe", "naver_web"):
        items = data.get(key, [])
        if isinstance(items, list):
            result[key] = [
                {"title": _clean_text(item.get("title", "")), "description": _clean_text(item.get("description", ""))}
                for item in items[:5]
                if isinstance(item, dict)
            ]

    # Exa results
    for key in ("exa_culture", "exa_strategy", "exa_tech"):
        items = data.get(key, [])
        if isinstance(items, list):
            result[key] = [
                {"title": item.get("title", ""), "text": item.get("text", "")[:200]}
                for item in items[:3]
                if isinstance(item, dict)
            ]

    # String values
    for k, v in data.items():
        if k not in result:
            result[k] = v

    return result


def _clean_news_item(item: dict[str, Any]) -> dict[str, str]:
    """Clean a news item dict for display."""
    return {
        "title": _clean_text(item.get("title", "")),
        "source": item.get("source", item.get("pub_date", "")),
        "link": item.get("link", item.get("url", "")),
    }


def _clean_text(text: str) -> str:
    """Remove HTML tags and excessive whitespace."""
    import re

    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _format_date(date_str: str) -> str:
    """Format YYYYMMDD to YYYY년 MM월 DD일."""
    if not date_str or len(date_str) < 8:
        return date_str or "—"
    try:
        return f"{date_str[:4]}년 {int(date_str[4:6])}월 {int(date_str[6:8])}일"
    except (ValueError, IndexError):
        return date_str


def _format_amount(amount_str: str) -> str:
    """Format large numbers to 억/조 units."""
    if not amount_str:
        return "—"
    # Remove commas
    clean = amount_str.replace(",", "").strip()
    try:
        num = int(clean)
        if abs(num) >= 1_000_000_000_000:
            return f"{num / 1_000_000_000_000:.1f}조"
        if abs(num) >= 100_000_000:
            return f"{num / 100_000_000:.0f}억"
        if abs(num) >= 10_000:
            return f"{num / 10_000:.0f}만"
        return f"{num:,}"
    except (ValueError, TypeError):
        return amount_str


def _parse_number(s: str | None) -> int:
    """Parse number from string, removing commas."""
    if not s:
        return 0
    try:
        return int(str(s).replace(",", "").strip())
    except (ValueError, TypeError):
        return 0
