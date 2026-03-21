"""Tests for LLM base protocol and NoLLM fallback."""

from hirekit.llm.base import BaseLLM, LLMResponse, NoLLM


class TestLLMResponse:
    def test_default_fields(self):
        resp = LLMResponse(text="hello")
        assert resp.text == "hello"
        assert resp.structured is None
        assert resp.model == ""
        assert resp.usage == {}

    def test_with_all_fields(self):
        resp = LLMResponse(
            text="output",
            structured={"key": "value"},
            model="gpt-4o",
            usage={"input_tokens": 100, "output_tokens": 200},
        )
        assert resp.structured["key"] == "value"
        assert resp.usage["input_tokens"] == 100


class TestNoLLM:
    def test_is_available_returns_false(self):
        llm = NoLLM()
        assert llm.is_available() is False

    def test_generate_returns_empty_text(self):
        llm = NoLLM()
        resp = llm.generate(prompt="analyze 카카오")
        assert resp.text == ""

    def test_generate_returns_model_none(self):
        llm = NoLLM()
        resp = llm.generate(prompt="test")
        assert resp.model == "none"

    def test_generate_ignores_all_parameters(self):
        llm = NoLLM()
        resp = llm.generate(
            prompt="test",
            system="system prompt",
            temperature=0.9,
            max_tokens=500,
            json_schema={"type": "object"},
        )
        assert resp.text == ""

    def test_nollm_is_subclass_of_base(self):
        assert issubclass(NoLLM, BaseLLM)
