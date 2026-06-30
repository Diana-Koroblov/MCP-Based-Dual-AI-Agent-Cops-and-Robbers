"""Cop MCP server — FastMCP server on port 8001.

Why a dedicated server per agent: the assignment requires two independent MCP
servers so each agent has an isolated message channel and its own auth token.
No game logic lives here; the server is a pure communication interface.

Run locally:
    uv run python -m src.mcp_servers.cop_server

Deploy on Render:
    Start command: uv run python -m src.mcp_servers.cop_server
    Env var:       COP_MCP_TOKEN=<strong-random-token>
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

__all__ = ["create_cop_mcp"]

log = logging.getLogger(__name__)


def create_cop_mcp(
    grid_size: list[int] | None = None,
) -> tuple[FastMCP, MessageStore]:
    """Build a FastMCP cop server with all three tools registered.

    Separating construction from ``__main__`` allows tests to create the
    server without running it and without needing real config files.

    Args:
        grid_size: Override board dimensions (default: loaded from config.json).

    Returns:
        ``(mcp, store)`` — store is exposed so callers can inspect/reset state.
    """
    if grid_size is None:
        grid_size = load_grid_size()

    store = MessageStore()
    mcp = FastMCP("cop-server")

    mcp.tool()(make_validate_position(grid_size))
    mcp.tool()(make_send_message(store))
    mcp.tool()(make_receive_message(store))

    log.info("cop-server tools registered (grid=%s).", grid_size)
    return mcp, store


if __name__ == "__main__":
    import uvicorn
    from dotenv import load_dotenv

    load_dotenv()

    _token = os.environ.get("COP_MCP_TOKEN", "")
    if not _token:
        raise RuntimeError("COP_MCP_TOKEN environment variable is not set.")

    _mcp, _ = create_cop_mcp()
    _port = int(os.environ.get("COP_PORT", "8001"))

    log.info("Starting cop-server on port %d.", _port)
    # Why wrap here and not in create_cop_mcp: auth is a deployment concern.
    # Tests call create_cop_mcp() without auth and test middleware separately.
    try:
        _asgi = TokenAuthMiddleware(_mcp.http_app(), token=_token)
    except AttributeError:
        # Older FastMCP 2.x used sse_app() instead of http_app()
        _asgi = TokenAuthMiddleware(_mcp.sse_app(), token=_token)

    uvicorn.run(_asgi, host="0.0.0.0", port=_port)
