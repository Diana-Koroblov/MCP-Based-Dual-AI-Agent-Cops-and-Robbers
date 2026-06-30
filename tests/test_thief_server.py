"""Tests for the thief MCP server.

The thief server uses the same tool implementations as the cop server,
so these tests focus on: (1) confirming all three tools work correctly
under the thief's configuration, and (2) verifying store isolation —
the thief's MessageStore is completely independent from the cop's.
"""

from __future__ import annotations

from src.mcp_servers.message_store import MessageStore
from src.mcp_servers.server_tools import (
    make_receive_message,
    make_send_message,
    make_validate_position,
)

# ---------------------------------------------------------------------------
# validate_position — thief-server configuration
# ---------------------------------------------------------------------------

def test_thief_validate_in_bounds():
    fn = make_validate_position([5, 5])
    assert fn(0, 0)["valid"] is True
    assert fn(4, 4)["valid"] is True


def test_thief_validate_out_of_bounds():
    fn = make_validate_position([5, 5])
    result = fn(5, 5)
    assert result["valid"] is False
    assert result["reason"] == "out_of_bounds"


def test_thief_validate_negative():
    fn = make_validate_position([5, 5])
    assert fn(-1, 0)["valid"] is False


# ---------------------------------------------------------------------------
# send_message / receive_message — thief-server round-trip
# ---------------------------------------------------------------------------

def test_thief_send_receive_roundtrip():
    store = MessageStore()
    text = "You'll never catch me, cop."
    make_send_message(store)(text)
    assert make_receive_message(store)()["message"] == text


def test_thief_receive_empty_before_send():
    store = MessageStore()
    assert make_receive_message(store)()["message"] is None


# ---------------------------------------------------------------------------
# Store isolation — cop and thief stores are fully independent
# ---------------------------------------------------------------------------

def test_thief_store_does_not_share_state_with_cop():
    """Sending a message to the cop store must NOT appear in the thief store."""
    cop_store = MessageStore()
    thief_store = MessageStore()

    make_send_message(cop_store)("Cop's secret message")

    thief_msg = make_receive_message(thief_store)()
    assert thief_msg["message"] is None, (
        "Thief store must not receive messages sent to the cop store."
    )


def test_cop_store_does_not_see_thief_message():
    """Sending a message to the thief store must NOT appear in the cop store."""
    cop_store = MessageStore()
    thief_store = MessageStore()

    make_send_message(thief_store)("I'm heading east.")

    cop_msg = make_receive_message(cop_store)()
    assert cop_msg["message"] is None


# ---------------------------------------------------------------------------
# create_thief_mcp — server factory (covers thief_server.py)
# ---------------------------------------------------------------------------

def test_create_thief_mcp_returns_mcp_and_store():
    """create_thief_mcp with explicit grid_size must not touch config files."""
    from src.mcp_servers.thief_server import create_thief_mcp

    mcp, store = create_thief_mcp(grid_size=[5, 5])
    assert mcp is not None
    assert isinstance(store, MessageStore)


def test_create_thief_mcp_store_starts_empty():
    from src.mcp_servers.thief_server import create_thief_mcp

    _, store = create_thief_mcp(grid_size=[5, 5])
    assert store.receive()["message"] is None
