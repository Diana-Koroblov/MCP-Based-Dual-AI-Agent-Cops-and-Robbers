"""Tests for MCPClient — typed wrappers with mocked httpx transport.

Strategy: patch httpx.Client (used as context manager inside _call)
so no real network calls are made. This covers validate_position,
send_message, receive_message, 401 auth error, and network errors.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from src.orchestrator.client import MCPAuthError, MCPCallError, MCPClient


# ---------------------------------------------------------------------------
# Helper — build a mock httpx response
# ---------------------------------------------------------------------------

def _mock_response(status: int, body: dict) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status
    resp.is_success = 200 <= status < 300
    resp.text = json.dumps(body)
    resp.json.return_value = body
    return resp


def _mcp_body(tool_result: dict) -> dict:
    """Wrap a tool result in the MCP JSON-RPC response envelope."""
    return {
        "result": {
            "content": [{"type": "text", "text": json.dumps(tool_result)}]
        }
    }


def _make_client(**kwargs) -> MCPClient:
    defaults = dict(
        cop_url="http://localhost:8001",
        thief_url="http://localhost:8002",
        cop_token="cop-tok",
        thief_token="thief-tok",
    )
    defaults.update(kwargs)
    return MCPClient(**defaults)


def _patch_httpx(response: MagicMock):
    """Return a context-manager patch that makes httpx.Client return *response*."""
    mock_http = MagicMock()
    mock_http.__enter__ = MagicMock(return_value=mock_http)
    mock_http.__exit__ = MagicMock(return_value=False)
    mock_http.post.return_value = response
    return patch("httpx.Client", return_value=mock_http), mock_http


# ---------------------------------------------------------------------------
# validate_position
# ---------------------------------------------------------------------------

def test_validate_position_valid():
    resp = _mock_response(200, _mcp_body({"valid": True, "reason": None}))
    patcher, mock_http = _patch_httpx(resp)
    with patcher:
        client = _make_client()
        result = client.validate_position("cop", 2, 3)
    assert result == {"valid": True, "reason": None}


def test_validate_position_out_of_bounds():
    resp = _mock_response(200, _mcp_body({"valid": False, "reason": "out_of_bounds"}))
    patcher, _ = _patch_httpx(resp)
    with patcher:
        result = _make_client().validate_position("thief", 9, 9)
    assert result["valid"] is False


def test_validate_position_sends_correct_tool_name():
    resp = _mock_response(200, _mcp_body({"valid": True, "reason": None}))
    patcher, mock_http = _patch_httpx(resp)
    with patcher:
        _make_client().validate_position("cop", 1, 1)
    payload = mock_http.post.call_args[1]["json"]
    assert payload["params"]["name"] == "validate_position"
    assert payload["params"]["arguments"] == {"x": 1, "y": 1}


# ---------------------------------------------------------------------------
# send_message
# ---------------------------------------------------------------------------

def test_send_message_returns_success():
    resp = _mock_response(200, _mcp_body({"success": True}))
    patcher, _ = _patch_httpx(resp)
    with patcher:
        result = _make_client().send_message("cop", "I'm closing in!")
    assert result == {"success": True}


def test_send_message_uses_correct_agent_url():
    resp = _mock_response(200, _mcp_body({"success": True}))
    patcher, mock_http = _patch_httpx(resp)
    with patcher:
        _make_client().send_message("thief", "Hiding northwest.")
    url_called = mock_http.post.call_args[0][0]
    assert "8002" in url_called  # thief URL


# ---------------------------------------------------------------------------
# receive_message
# ---------------------------------------------------------------------------

def test_receive_message_returns_dict():
    resp = _mock_response(200, _mcp_body({"message": "heading east", "turn": None}))
    patcher, _ = _patch_httpx(resp)
    with patcher:
        result = _make_client().receive_message("cop")
    assert result["message"] == "heading east"


def test_receive_message_empty():
    resp = _mock_response(200, _mcp_body({"message": None, "turn": None}))
    patcher, _ = _patch_httpx(resp)
    with patcher:
        result = _make_client().receive_message("thief")
    assert result["message"] is None


# ---------------------------------------------------------------------------
# Auth and error handling
# ---------------------------------------------------------------------------

def test_401_raises_mcp_auth_error():
    resp = _mock_response(401, {})
    patcher, _ = _patch_httpx(resp)
    with patcher:
        with pytest.raises(MCPAuthError, match="401"):
            _make_client().validate_position("cop", 0, 0)


def test_500_raises_mcp_call_error():
    resp = _mock_response(500, {})
    patcher, _ = _patch_httpx(resp)
    with patcher:
        with pytest.raises(MCPCallError, match="500"):
            _make_client().send_message("cop", "hello")


def test_network_error_raises_mcp_call_error():
    import httpx as _httpx

    mock_http = MagicMock()
    mock_http.__enter__ = MagicMock(return_value=mock_http)
    mock_http.__exit__ = MagicMock(return_value=False)
    mock_http.post.side_effect = _httpx.ConnectError("refused")

    with patch("httpx.Client", return_value=mock_http):
        with pytest.raises(MCPCallError, match="Network error"):
            _make_client().validate_position("cop", 0, 0)


# ---------------------------------------------------------------------------
# Auth token injection
# ---------------------------------------------------------------------------

def test_cop_token_sent_in_header():
    resp = _mock_response(200, _mcp_body({"valid": True, "reason": None}))
    patcher, mock_http = _patch_httpx(resp)
    with patcher:
        _make_client(cop_token="my-cop-secret").validate_position("cop", 0, 0)
    headers = mock_http.post.call_args[1]["headers"]
    assert headers["Authorization"] == "Bearer my-cop-secret"


def test_thief_token_sent_in_header():
    resp = _mock_response(200, _mcp_body({"success": True}))
    patcher, mock_http = _patch_httpx(resp)
    with patcher:
        _make_client(thief_token="my-thief-secret").send_message("thief", "hi")
    headers = mock_http.post.call_args[1]["headers"]
    assert headers["Authorization"] == "Bearer my-thief-secret"


# ---------------------------------------------------------------------------
# Fallback parsing — malformed JSON-RPC envelope
# ---------------------------------------------------------------------------

def test_malformed_envelope_returns_raw_result():
    """If the JSON-RPC envelope is unexpected, _call falls back to data['result']."""
    body = {"result": "plain-string"}
    resp = _mock_response(200, body)
    patcher, _ = _patch_httpx(resp)
    with patcher:
        result = _make_client().validate_position("cop", 0, 0)
    assert result == "plain-string"
