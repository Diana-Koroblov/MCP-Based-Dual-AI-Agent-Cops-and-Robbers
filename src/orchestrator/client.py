"""MCP client — typed wrappers around both FastMCP servers.

Why a dedicated module: the orchestrator never calls httpx directly;
going through this client makes it easy to swap in a mock for testing
or point to Render URLs for deployment without touching call-sites.
"""

from __future__ import annotations

import json
import logging
from typing import Any

__all__ = ["MCPClient", "MCPAuthError", "MCPCallError"]

log = logging.getLogger(__name__)

# FastMCP 2.x HTTP app mounts the JSON-RPC handler at this path.
_MCP_PATH = "/mcp/"


class MCPAuthError(Exception):
    """Raised when the server returns HTTP 401 Unauthorized."""


class MCPCallError(Exception):
    """Raised when a tool call fails for a non-auth reason."""


class MCPClient:
    """Synchronous wrapper around both cop and thief MCP servers.

    Why synchronous: the turn loop is single-threaded; propagating
    async through the entire call stack adds complexity with no gain.

    Args:
        cop_url: Base URL of the cop MCP server (e.g. http://localhost:8001).
        thief_url: Base URL of the thief MCP server.
        cop_token: Bearer token for the cop server.
        thief_token: Bearer token for the thief server.
        timeout: Per-request timeout in seconds.
    """

    def __init__(
        self,
        cop_url: str,
        thief_url: str,
        cop_token: str,
        thief_token: str,
        timeout: float = 10.0,
    ) -> None:
        self._base: dict[str, str] = {
            "cop": cop_url.rstrip("/"),
            "thief": thief_url.rstrip("/"),
        }
        self._tokens: dict[str, str] = {
            "cop": cop_token,
            "thief": thief_token,
        }
        self._timeout = timeout

    # ------------------------------------------------------------------
    # Internal JSON-RPC helper
    # ------------------------------------------------------------------

    def _call(self, agent: str, tool: str, arguments: dict[str, Any]) -> Any:
        """Send a JSON-RPC tool-call to *agent*'s server and return the result.

        Raises:
            MCPAuthError: Server returns 401.
            MCPCallError: Any other non-2xx response or network error.
        """
        import httpx  # lazy import so unit tests can patch before first use

        url = self._base[agent] + _MCP_PATH
        headers = {"Authorization": f"Bearer {self._tokens[agent]}"}
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": tool, "arguments": arguments},
        }
        log.debug("MCP → %s %s %s", agent, tool, arguments)
        try:
            with httpx.Client(timeout=self._timeout) as http:
                resp = http.post(url, json=payload, headers=headers)
        except httpx.RequestError as exc:
            raise MCPCallError(f"Network error calling {agent}/{tool}: {exc}") from exc

        if resp.status_code == 401:
            raise MCPAuthError(f"{agent} server rejected auth token (401).")
        if not resp.is_success:
            raise MCPCallError(
                f"{agent}/{tool} returned HTTP {resp.status_code}: {resp.text[:200]}"
            )

        data = resp.json()
        # MCP JSON-RPC wraps tool output in result.content[0].text
        try:
            text = data["result"]["content"][0]["text"]
            return json.loads(text)
        except (KeyError, IndexError, json.JSONDecodeError):
            return data.get("result", data)

    # ------------------------------------------------------------------
    # Typed tool wrappers
    # ------------------------------------------------------------------

    def validate_position(self, agent: str, x: int, y: int) -> dict:
        """Return ``{"valid": bool, "reason": str | None}``."""
        return self._call(agent, "validate_position", {"x": x, "y": y})

    def send_message(self, agent: str, text: str) -> dict:
        """Store *text* in the server's message store; return ``{"success": True}``."""
        log.debug("[%s] send_message: %r", agent, text)
        return self._call(agent, "send_message", {"text": text})

    def receive_message(self, agent: str) -> dict:
        """Return ``{"message": str | None, "turn": int | None}``."""
        result = self._call(agent, "receive_message", {})
        log.debug("[%s] receive_message → %r", agent, result)
        return result
