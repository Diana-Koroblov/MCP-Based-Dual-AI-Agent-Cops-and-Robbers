"""Thief MCP server — FastMCP server on port 8002.

Mirrors cop_server.py exactly, but uses a separate FastMCP instance,
its own MessageStore, and the THIEF_MCP_TOKEN environment variable.
This guarantees complete isolation: the cop cannot read the thief's
message store and vice-versa.

Run locally:
    uv run python -m src.mcp_servers.thief_server

Deploy on Render:
    Start command: uv run python -m src.mcp_servers.thief_server
    Env var:       THIEF_MCP_TOKEN=<strong-random-token>
"""

from __future__ import annotations

import logging
import os

from fastmcp import FastMCP

from src.mcp_servers.auth_middleware import TokenAuthMiddleware
from src.mcp_servers.message_store import MessageStore
from src.mcp_servers.server_tools import (
    load_grid_size,
    make_receive_message,
    make_send_message,
    make_validate_position,
)

__all__ = ["create_thief_mcp"]

log = logging.getLogger(__name__)


def create_thief_mcp(
    grid_size: list[int] | None = None,
) -> tuple[FastMCP, MessageStore]:
    """Build a FastMCP thief server with all three tools registered.

    Args:
        grid_size: Override board dimensions (default: loaded from config.json).

    Returns:
        ``(mcp, store)`` — store is exposed so callers can inspect/reset state.
    """
    if grid_size is None:
        grid_size = load_grid_size()

    store = MessageStore()
    mcp = FastMCP("thief-server")

    mcp.tool()(make_validate_position(grid_size))
    mcp.tool()(make_send_message(store))
    mcp.tool()(make_receive_message(store))

    log.info("thief-server tools registered (grid=%s).", grid_size)
    return mcp, store


if __name__ == "__main__":
    import uvicorn
    from dotenv import load_dotenv

    load_dotenv()

    _token = os.environ.get("THIEF_MCP_TOKEN", "")
    if not _token:
        raise RuntimeError("THIEF_MCP_TOKEN environment variable is not set.")

    _mcp, _ = create_thief_mcp()
    _port = int(os.environ.get("THIEF_PORT", "8002"))

    log.info("Starting thief-server on port %d.", _port)
    try:
        _asgi = TokenAuthMiddleware(_mcp.http_app(), token=_token)
    except AttributeError:
        _asgi = TokenAuthMiddleware(_mcp.sse_app(), token=_token)

    uvicorn.run(_asgi, host="0.0.0.0", port=_port)
