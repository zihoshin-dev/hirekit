"""Sectioned LLM analysis pipeline — multi-step, section-by-section."""

from __future__ import annotations

import logging
from typing import Any

from hirekit.llm.base import BaseLLM
from hirekit.sources.base import SourceResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompts (constants)
# ---------------------------------------------------------------------------

_SYSTEM_FACT_EXTRACTOR = (
    "당신은 기업 분석 전문가예요. 수집된 원시 데이터에서 핵심 사실만 추출해주세요.\n"
    "규칙: 데이터에 없는 내용은 절대 만들지 마세요. 각 사실에 출처를 명시해주세요."
)

_SYSTEM_SECTION_OVERVIEW = (
    "당신은 취업 준비자를 위한 기업 분석 전문가예요.\n"
    "아래 사실들을 바탕으로 회사 개요를 작성해주세요.\n"
    "포함할 것: 설립/대표/직원수/연봉/핵심 실적/주요 서비스\n"
    "없는 정보는 생략하세요. 해요체로 작성해주세요."
)

_SYSTEM_SECTION_INDUSTRY = (
    "당신은 산업 분석 전문가예요.\n"
    "아래 사실들을 바탕으로 이 기업의 산업 포지셔닝과 경쟁 환경을 분석해주세요.\n"
    "포함할 것: 시장 위치/주요 경쟁사/차별화 포인트/성장 기회와 위협\n"
    "해요체로 작성해주세요."
)

_SYSTEM_SECTION_TECH = (
    "당신은 기술 트렌드 분석 전문가예요.\n"
    "아래 사실들을 바탕으로 이 기업의 AI 전략과 기술 동향을 분석해주세요.\n"
    "포함할 것: 기술 스택/AI 투자 현황/오픈소스 활동/기술 방향성\n"
    "해요체로 작성해주세요."
)

_SYSTEM_SECTION_VERDICT = (
    "당신은 커리어 전략 컨설턴트예요.\n"
    "아래 분석 결과를 종합하여 이 회사에 지원해야 하는지 판단해주세요.\n"
    "Go(65+)/Hold(40-64)/Pass(<40) 중 하나를 선택하고 근거를 제시해주세요.\n"
    "포함할 것: 종합 판정/핵심 강점 3개/주요 리스크 3개/추천 포지션\n"
    "해요체로 작성해주세요."
)

_SYSTEM_SPEED_SHEET = (
    "당신은 취업 전략 전문가예요.\n"
    "아래 분석을 바탕으로 면접 전 30초 브리핑용 스피드 시트를 작성해주세요.\n"
    "포맷: 한 줄 회사 설명 / 핵심 숫자 3개 / 면접 포인트 3개 / 결론 한 줄\n"
    "해요체로 간결하게 작성해주세요."
)

# Sections to include in fact extraction (section key → label)
_SECTION_LABELS: dict[str, str] = {
    "overview": "회사 개요",
    "financials": "재무",
    "industry": "산업/경쟁",
    "competition": "경쟁사",
    "leadership": "리더십",
    "strategy": "전략",
    "culture": "문화/복지",
    "ai": "AI/기술",
    "tech": "기술 스택",
    "regulation": "규제/컴플라이언스",
    "policy": "정책",
    "role": "채용/포지션",
}


class LLMPipeline:
    """섹션별 다단계 LLM 분석."""

    def __init__(self, llm: BaseLLM) -> None:
        self.llm = llm

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(self, raw_results: list[SourceResult], company: str) -> dict[int, Any]:
        """수집 데이터 → 구조화 분석 결과 반환.

        Returns
        -------
        dict[int, Any]
            Section number → analysis text. Empty dict when LLM unavailable.
        """
        if not self.llm.is_available():
            return {}

        # Step 1: Fact Extraction
        facts = self._extract_facts(raw_results, company)
        if not facts:
            return {}

        # Step 2: Section Analysis (핵심 4개 섹션)
        sections: dict[int, Any] = {}

        sections[1] = self._analyze_section_overview(facts, company)
        sections[2] = self._analyze_section_industry(facts, company)
        sections[7] = self._analyze_section_tech(facts, company)
        sections[11] = self._analyze_section_verdict(facts, company, sections)

        # Step 3: Speed Sheet
        sections[0] = self._generate_speed_sheet(company, sections)

        return sections

    # ------------------------------------------------------------------
    # Step 1: Fact Extraction
    # ------------------------------------------------------------------

    def _extract_facts(self, raw_results: list[SourceResult], company: str) -> str:
        """수집 데이터에서 핵심 사실 추출."""
        raw_chunks: list[str] = []
        for r in raw_results:
            if not r.raw:
                continue
            label = _SECTION_LABELS.get(r.section, r.section)
            chunk = f"[출처: {r.source_name} / {label}]\n{r.raw[:800]}"
            raw_chunks.append(chunk)

        if not raw_chunks:
            return ""

        combined = "\n\n".join(raw_chunks)
        # cap total input to keep within token budget
        combined = combined[:6000]

        prompt = (
            f"기업명: {company}\n\n"
            f"수집된 데이터:\n{combined}\n\n"
            "위 데이터에서 핵심 사실을 항목별로 추출해주세요. "
            "각 사실 끝에 [출처: source_name] 형식으로 출처를 붙여주세요."
        )

        try:
            resp = self.llm.generate(
                prompt=prompt,
                system=_SYSTEM_FACT_EXTRACTOR,
                temperature=0.1,
                max_tokens=1500,
            )
            return resp.text or ""
        except Exception:
            logger.warning("Fact extraction failed", exc_info=True)
            return ""

    # ------------------------------------------------------------------
    # Step 2: Section analyses
    # ------------------------------------------------------------------

    def _analyze_section_overview(self, facts: str, company: str) -> str:
        """Section 1: 회사 개요."""
        return self._call_section(
            section_name="회사 개요",
            facts=facts,
            company=company,
            system=_SYSTEM_SECTION_OVERVIEW,
            focus_keywords=["설립", "대표", "직원", "연봉", "매출", "서비스", "제품"],
        )

    def _analyze_section_industry(self, facts: str, company: str) -> str:
        """Section 2: 산업 포지셔닝."""
        return self._call_section(
            section_name="산업 포지셔닝 & 경쟁",
            facts=facts,
            company=company,
            system=_SYSTEM_SECTION_INDUSTRY,
            focus_keywords=["경쟁", "시장", "점유율", "업계", "포지션", "성장"],
        )

    def _analyze_section_tech(self, facts: str, company: str) -> str:
        """Section 7: AI 전략 & 기술."""
        return self._call_section(
            section_name="AI 전략 & 기술 트렌드",
            facts=facts,
            company=company,
            system=_SYSTEM_SECTION_TECH,
            focus_keywords=["AI", "기술", "스택", "GitHub", "오픈소스", "개발"],
        )

    def _analyze_section_verdict(
        self,
        facts: str,
        company: str,
        prior_sections: dict[int, Any],
    ) -> str:
        """Section 11: 종합 판단."""
        # Build summary of prior section outputs
        prior_summary_parts: list[str] = []
        labels = {1: "회사 개요", 2: "산업 포지셔닝", 7: "AI/기술"}
        for num, label in labels.items():
            text = prior_sections.get(num, "")
            if text:
                prior_summary_parts.append(f"[{label}]\n{str(text)[:600]}")

        prior_summary = "\n\n".join(prior_summary_parts)

        prompt = (
            f"기업명: {company}\n\n"
            f"섹션별 분석 요약:\n{prior_summary}\n\n"
            f"추가 수집 데이터:\n{facts[:1500]}\n\n"
            "위 내용을 종합하여 Go/Hold/Pass 판정과 근거를 작성해주세요."
        )

        try:
            resp = self.llm.generate(
                prompt=prompt,
                system=_SYSTEM_SECTION_VERDICT,
                temperature=0.2,
                max_tokens=1500,
            )
            return resp.text or ""
        except Exception:
            logger.warning("Section 11 (verdict) analysis failed", exc_info=True)
            return ""

    # ------------------------------------------------------------------
    # Step 3: Speed Sheet
    # ------------------------------------------------------------------

    def _generate_speed_sheet(self, company: str, sections: dict[int, Any]) -> str:
        """Section 0: 스피드 시트 (면접 30초 브리핑)."""
        overview = str(sections.get(1, ""))[:500]
        verdict = str(sections.get(11, ""))[:500]

        prompt = (
            f"기업명: {company}\n\n"
            f"회사 개요:\n{overview}\n\n"
            f"종합 판단:\n{verdict}\n\n"
            "위 내용을 바탕으로 스피드 시트를 작성해주세요."
        )

        try:
            resp = self.llm.generate(
                prompt=prompt,
                system=_SYSTEM_SPEED_SHEET,
                temperature=0.2,
                max_tokens=800,
            )
            return resp.text or ""
        except Exception:
            logger.warning("Speed sheet generation failed", exc_info=True)
            return ""

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _call_section(
        self,
        section_name: str,
        facts: str,
        company: str,
        system: str,
        focus_keywords: list[str],
    ) -> str:
        """해당 섹션 키워드 관련 사실만 필터링 후 LLM 호출."""
        # Filter fact lines relevant to this section
        filtered_lines: list[str] = []
        for line in facts.splitlines():
            if any(kw.lower() in line.lower() for kw in focus_keywords):
                filtered_lines.append(line)

        # Fall back to full facts if filtering yields nothing
        filtered = "\n".join(filtered_lines) if filtered_lines else facts
        filtered = filtered[:3000]

        prompt = (
            f"기업명: {company}\n"
            f"분석 섹션: {section_name}\n\n"
            f"관련 사실:\n{filtered}\n\n"
            "위 사실을 바탕으로 분석을 작성해주세요."
        )

        try:
            resp = self.llm.generate(
                prompt=prompt,
                system=system,
                temperature=0.2,
                max_tokens=1500,
            )
            return resp.text or ""
        except Exception:
            logger.warning("Section '%s' analysis failed", section_name, exc_info=True)
            return ""
