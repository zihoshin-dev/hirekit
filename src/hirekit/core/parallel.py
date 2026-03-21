"""Parallel data collection executor."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from hirekit.sources.base import BaseSource, SourceResult

logger = logging.getLogger(__name__)


def collect_parallel(
    sources: list[BaseSource],
    company: str,
    max_workers: int = 5,
    **kwargs: Any,
) -> list[SourceResult]:
    """Run multiple data source collectors in parallel.

    Returns all successfully collected results. Failed sources are logged and skipped.
    """
    all_results: list[SourceResult] = []

    def _run_source(source: BaseSource) -> list[SourceResult]:
        try:
            return source.collect(company, **kwargs)
        except Exception as e:
            logger.warning("Source %s failed for %s: %s", source.name, company, e)
            return []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_run_source, s): s for s in sources}

        for future in as_completed(futures):
            source = futures[future]
            try:
                results = future.result(timeout=source.get_timeout())
                all_results.extend(results)
                logger.info("Source %s: %d results", source.name, len(results))
            except TimeoutError:
                logger.warning("Source %s timed out after %ds", source.name, source.get_timeout())
            except Exception as e:
                logger.warning("Source %s error: %s", source.name, e)

    return all_results
