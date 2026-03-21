"""Shared test fixtures for HireKit."""

import pytest

from hirekit.core.config import HireKitConfig
from hirekit.sources.base import SourceResult


@pytest.fixture
def default_config():
    """Default HireKit configuration for tests."""
    return HireKitConfig()


@pytest.fixture
def sample_source_result():
    """Sample source result for testing."""
    return SourceResult(
        source_name="test_source",
        section="overview",
        data={"company_name": "TestCorp", "ceo": "Test CEO"},
        confidence=0.9,
        url="https://example.com",
        raw="TestCorp is a test company.",
    )
