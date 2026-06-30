"""Tests for LLMLoop — prompt sending and error handling.

Strategy: inject a mock gateway so no real Gemini calls are made.
Tests also cover the default_gateway error path via genai mocking.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.orchestrator.llm_loop import LLMError, LLMLoop


# ---------------------------------------------------------------------------
# ask() — happy path with mock gateway
# ---------------------------------------------------------------------------

def test_ask_returns_gateway_response():
    loop = LLMLoop(gateway=lambda _p: "ACTION: N\nMESSAGE: Going north.")
    assert loop.ask("Some prompt") == "ACTION: N\nMESSAGE: Going north."


def test_ask_strips_leading_trailing_whitespace():
    loop = LLMLoop(gateway=lambda _p: "  ACTION: E  ")
    # gateway return is passed through as-is (stripping is gateway's job)
    result = loop.ask("prompt")
    assert result == "  ACTION: E  "


def test_ask_logs_char_counts(caplog):
    import logging
    loop = LLMLoop(gateway=lambda _p: "response text")
    with caplog.at_level(logging.DEBUG, logger="src.orchestrator.llm_loop"):
        loop.ask("hello")
    assert any("chars" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# ask() — error cases
# ---------------------------------------------------------------------------

def test_ask_empty_prompt_raises():
    loop = LLMLoop(gateway=lambda _p: "ok")
    with pytest.raises(LLMError, match="empty"):
        loop.ask("")


def test_ask_whitespace_only_prompt_raises():
    loop = LLMLoop(gateway=lambda _p: "ok")
    with pytest.raises(LLMError, match="empty"):
        loop.ask("   ")


def test_ask_empty_gateway_response_raises():
    loop = LLMLoop(gateway=lambda _p: "")
    with pytest.raises(LLMError):
        loop.ask("Some prompt")


def test_ask_whitespace_gateway_response_raises():
    loop = LLMLoop(gateway=lambda _p: "   ")
    with pytest.raises(LLMError):
        loop.ask("Some prompt")


def test_gateway_exception_propagates():
    def bad_gateway(_p):
        raise LLMError("API down")

    loop = LLMLoop(gateway=bad_gateway)
    with pytest.raises(LLMError, match="API down"):
        loop.ask("prompt")


# ---------------------------------------------------------------------------
# default_gateway — Gemini API call via mocked google.generativeai
# ---------------------------------------------------------------------------

def test_default_gateway_calls_genai():
    mock_model_inst = MagicMock()
    mock_model_inst.generate_content.return_value = MagicMock(text="Go east!")

    with patch("google.generativeai.GenerativeModel", return_value=mock_model_inst):
        loop = LLMLoop(model="gemini-1.5-flash")
        result = loop._default_gateway("test prompt")

    assert result == "Go east!"
    mock_model_inst.generate_content.assert_called_once_with("test prompt")


def test_default_gateway_raises_on_api_error():
    mock_model_inst = MagicMock()
    mock_model_inst.generate_content.side_effect = RuntimeError("quota exceeded")

    with patch("google.generativeai.GenerativeModel", return_value=mock_model_inst):
        loop = LLMLoop()
        with pytest.raises(LLMError, match="Gemini API error"):
            loop._default_gateway("test prompt")


def test_default_gateway_raises_on_empty_text():
    mock_model_inst = MagicMock()
    mock_model_inst.generate_content.return_value = MagicMock(text="")

    with patch("google.generativeai.GenerativeModel", return_value=mock_model_inst):
        loop = LLMLoop()
        with pytest.raises(LLMError, match="empty"):
            loop._default_gateway("test prompt")


# ---------------------------------------------------------------------------
# LLMLoop instantiation
# ---------------------------------------------------------------------------

def test_custom_model_stored():
    loop = LLMLoop(model="gemini-ultra", gateway=lambda _p: "ok")
    assert loop._model == "gemini-ultra"


def test_custom_gateway_used():
    calls = []

    def my_gateway(prompt):
        calls.append(prompt)
        return "response"

    loop = LLMLoop(gateway=my_gateway)
    loop.ask("hello world")
    assert calls == ["hello world"]
