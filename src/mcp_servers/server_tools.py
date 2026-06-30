"""Factory functions that produce the three MCP tool callables.

Why factories (closures) instead of plain functions: each server needs its own
MessageStore instance and its own grid_size baked in.  A factory captures these
at server-startup time so every tool call avoids re-reading config and re-looking
up the store on the hot path.

Tools exposed by both Cop and Thief servers:
    validate_position(x, y)   — bounds check only; barriers tracked by engine
    send_message(text)        — store a free-form NL message
    receive_message()         — retrieve the opponent's latest NL message
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from pathlib import Path

from src.mcp_servers.message_store import MessageStore

__all__ = [
    "load_grid_size",
    "make_validate_position",
    "make_send_message",
    "make_receive_message",
]

log = logging.getLogger(__name__)

# Resolved at import time so tests that override grid_size don't need the file.
_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "config.json"


def load_grid_size(config_path: Path = _CONFIG_PATH) -> list[int]:
    """Return ``[rows, cols]`` from ``config/config.json``.

    Raises:
        FileNotFoundError: if config file is absent.
        KeyError: if ``grid_size`` key is missing.
    """
    with config_path.open() as fh:
        data = json.load(fh)
    grid = data["grid_size"]
    log.debug("Loaded grid_size=%s from %s.", grid, config_path)
    return grid


def make_validate_position(grid_size: list[int]) -> Callable[[int, int], dict]:
    """Return a ``validate_position(x, y)`` callable for *grid_size*.

    The server validates grid bounds only — barrier state lives in the game
    engine and is never replicated to the MCP server.

    Args:
        grid_size: ``[rows, cols]`` list from config.

    Returns:
        Callable that accepts (x: int, y: int) and returns a dict.
    """
    rows, cols = grid_size

    def validate_position(x: int, y: int) -> dict:
        """Check whether cell (x, y) is within the board boundaries."""
        if 0 <= x < cols and 0 <= y < rows:
            log.debug("validate_position(%d, %d) → valid", x, y)
            return {"valid": True, "reason": None}
        log.debug("validate_position(%d, %d) → out_of_bounds", x, y)
        return {"valid": False, "reason": "out_of_bounds"}

    return validate_position


def make_send_message(store: MessageStore) -> Callable[[str], dict]:
    """Return a ``send_message(text)`` callable backed by *store*."""

    def send_message(text: str) -> dict:
        """Store a free-form NL message from this agent for the opponent."""
        return store.send(text)

    return send_message


def make_receive_message(store: MessageStore) -> Callable[[], dict]:
    """Return a ``receive_message()`` callable backed by *store*."""

    def receive_message() -> dict:
        """Retrieve the opponent's latest NL message (nulls if none sent yet)."""
        return store.receive()

    return receive_message
