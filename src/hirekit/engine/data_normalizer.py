"""Normalize raw source data into template-ready format."""

from __future__ import annotations

from typing import Any


def normalize_sections(sections: dict[int, dict[str, Any]]) -> dict[int, dict[str, Any]]:
    """Transform raw source data into clean template variables.

    Bridges the gap between SourceResult.data (raw API output)
    and report_ko.md.j2 template expectations.
    """
    normalized: dict[int, dict[str, Any]] = {}

    for num, data in sections.items():
        if not isinstance(data, dict):
            normalized[num] = data
            continue
        normalized[num] = _normalize_section(num, data)

    return normalized


def _normalize_section(num: int, data: dict[str, Any]) -> dict[str, Any]:
    """Normalize a single section's data."""
    result = dict(data)  # shallow copy

    if num == 1:
        result = _normalize_overview(result)
    elif num == 4:
        result = _normalize_culture(result)

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
                        f"{emp.get('position', '')} {emp.get('gender', '')}: "
                        f"정규직 {emp.get('headcount', '')}명"
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
    for key in ("recent_news", "google_news", "korean_credible_news",
                "international_news", "brave_web_results"):
        items = data.get(key, [])
        if isinstance(items, list):
            result[key] = [
                _clean_news_item(item) for item in items[:5]
                if isinstance(item, dict)
            ]

    # Pass through string values
    for k, v in data.items():
        if k not in result and isinstance(v, str):
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
                {"title": _clean_text(item.get("title", "")),
                 "description": _clean_text(item.get("description", ""))}
                for item in items[:5]
                if isinstance(item, dict)
            ]

    # Exa results
    for key in ("exa_culture", "exa_strategy", "exa_tech"):
        items = data.get(key, [])
        if isinstance(items, list):
            result[key] = [
                {"title": item.get("title", ""),
                 "text": item.get("text", "")[:200]}
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


def _parse_number(s: str) -> int:
    """Parse number from string, removing commas."""
    if not s:
        return 0
    try:
        return int(str(s).replace(",", "").strip())
    except (ValueError, TypeError):
        return 0
