"""Tests for the cop MCP server: tools, auth middleware, and thread safety.

Strategy: test tool functions as plain Python callables (no HTTP overhead),
and test TokenAuthMiddleware with a minimal Starlette mock app so auth
behaviour can be verified without booting a real FastMCP server.
"""

from __future__ import annotations

import threading

import pytest
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from src.mcp_servers.auth_middleware import TokenAuthMiddleware
from src.mcp_servers.message_store import MessageStore
from src.mcp_servers.server_tools import (
    make_receive_message,
    make_send_message,
    make_validate_position,
)

# ---------------------------------------------------------------------------
# validate_position — happy path and boundary checks
# ---------------------------------------------------------------------------

def test_validate_position_center():
    fn = make_validate_position([5, 5])
    result = fn(2, 3)
    assert result["valid"] is True
    assert result["reason"] is None


def test_validate_position_top_left_corner():
    fn = make_validate_position([5, 5])
    assert fn(0, 0)["valid"] is True


def test_validate_position_bottom_right_corner():
    fn = make_validate_position([5, 5])
    assert fn(4, 4)["valid"] is True


def test_validate_position_x_out_of_bounds():
    fn = make_validate_position([5, 5])
    result = fn(5, 0)
    assert result["valid"] is False
    assert result["reason"] == "out_of_bounds"


def test_validate_position_y_out_of_bounds():
    fn = make_validate_position([5, 5])
    result = fn(0, 5)
    assert result["valid"] is False
    assert result["reason"] == "out_of_bounds"


def test_validate_position_negative_coords():
    fn = make_validate_position([5, 5])
    assert fn(-1, 2)["valid"] is False
    assert fn(2, -1)["valid"] is False


def test_validate_position_non_square_grid():
    fn = make_validate_position([3, 7])  # 3 rows, 7 cols
    assert fn(6, 2)["valid"] is True   # x=6 < cols=7, y=2 < rows=3
    assert fn(7, 0)["valid"] is False  # x=7 == cols — out of bounds


# ---------------------------------------------------------------------------
# send_message / receive_message — round-trip and edge cases
# ---------------------------------------------------------------------------

def test_send_message_returns_success():
    store = MessageStore()
    send = make_send_message(store)
    assert send("Heading north to cut off your escape.") == {"success": True}


def test_receive_before_send_returns_nulls():
    store = MessageStore()
    recv = make_receive_message(store)
    result = recv()
    assert result["message"] is None
    assert result["turn"] is None


def test_send_then_receive_roundtrip():
    store = MessageStore()
    text = "I'm closing in from the northwest."
    make_send_message(store)(text)
    result = make_receive_message(store)()
    assert result["message"] == text


def test_second_send_overwrites_first():
    store = MessageStore()
    send = make_send_message(store)
    recv = make_receive_message(store)
    send("First message")
    send("Second message")
    assert recv()["message"] == "Second message"


def test_reset_clears_message():
    store = MessageStore()
    store.send("Some text")
    store.reset()
    assert store.receive()["message"] is None


# ---------------------------------------------------------------------------
# Thread safety — two concurrent send_message calls
# ---------------------------------------------------------------------------

def test_concurrent_send_no_corruption():
    """Two threads calling send_message simultaneously must not corrupt state."""
    store = MessageStore()
    results: list[dict] = []
    errors: list[Exception] = []

    def sender(text: str) -> None:
        try:
            r = store.send(text)
            results.append(r)
        except Exception as exc:
            errors.append(exc)

    t1 = threading.Thread(target=sender, args=("Thread A — heading east",))
    t2 = threading.Thread(target=sender, args=("Thread B — heading west",))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert not errors, f"Exceptions raised in threads: {errors}"
    assert len(results) == 2
    assert all(r == {"success": True} for r in results)
    # Final stored value must be exactly one of the two messages — no torn state.
    final = store.receive()["message"]
    assert final in ("Thread A — heading east", "Thread B — heading west")


# ---------------------------------------------------------------------------
# TokenAuthMiddleware — 401 scenarios
# ---------------------------------------------------------------------------

async def _ok_endpoint(request):
    return JSONResponse({"ok": True})


_mock_starlette_app = Starlette(routes=[Route("/probe", _ok_endpoint)])

_TOKEN = "super-secret-cop-token"


@pytest.fixture()
def auth_client() -> TestClient:
    """TestClient for the mock ASGI app wrapped with token auth."""
    app = TokenAuthMiddleware(_mock_starlette_app, token=_TOKEN)
    return TestClient(app, raise_server_exceptions=False)


def test_valid_token_passes(auth_client):
    r = auth_client.get("/probe", headers={"Authorization": f"Bearer {_TOKEN}"})
    assert r.status_code == 200


def test_missing_auth_header_returns_401(auth_client):
    r = auth_client.get("/probe")
    assert r.status_code == 401


def test_wrong_token_returns_401(auth_client):
    r = auth_client.get("/probe", headers={"Authorization": "Bearer wrong-token"})
    assert r.status_code == 401


def test_no_bearer_prefix_returns_401(auth_client):
    r = auth_client.get("/probe", headers={"Authorization": _TOKEN})
    assert r.status_code == 401


def test_empty_token_raises_on_init():
    with pytest.raises(ValueError, match="empty"):
        TokenAuthMiddleware(_mock_starlette_app, token="")


# ---------------------------------------------------------------------------
# create_cop_mcp — server factory (covers cop_server.py)
# ---------------------------------------------------------------------------

def test_create_cop_mcp_returns_mcp_and_store():
    """create_cop_mcp with explicit grid_size must not touch config files."""
    from src.mcp_servers.cop_server import create_cop_mcp

    mcp, store = create_cop_mcp(grid_size=[5, 5])
    assert mcp is not None
    assert isinstance(store, MessageStore)


def test_create_cop_mcp_store_starts_empty():
    from src.mcp_servers.cop_server import create_cop_mcp

    _, store = create_cop_mcp(grid_size=[5, 5])
    assert store.receive()["message"] is None


# ---------------------------------------------------------------------------
# load_grid_size — reads grid dimensions from config file
# ---------------------------------------------------------------------------

def test_load_grid_size_reads_json(tmp_path):
    """load_grid_size must return the grid_size list from a JSON file."""
    import json

    from src.mcp_servers.server_tools import load_grid_size

    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({"grid_size": [4, 6]}))
    assert load_grid_size(cfg) == [4, 6]


def test_load_grid_size_missing_file(tmp_path):
    from src.mcp_servers.server_tools import load_grid_size

    with pytest.raises(FileNotFoundError):
        load_grid_size(tmp_path / "nonexistent.json")
