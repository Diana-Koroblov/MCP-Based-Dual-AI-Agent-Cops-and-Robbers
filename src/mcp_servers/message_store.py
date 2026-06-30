"""Thread-safe message store for MCP server inter-agent communication.

Why a dedicated module: both servers share the same locking pattern, but each
server gets its own MessageStore *instance* so their message channels never
bleed into each other.
"""

from __future__ import annotations

import logging
import threading

__all__ = ["MessageStore"]

log = logging.getLogger(__name__)


class MessageStore:
    """Stores the latest free-form NL message from one agent.

    Why threading.Lock here: FastMCP handles each HTTP request in its own
    thread. Without a lock, two simultaneous ``send_message`` calls could
    interleave writes and leave ``_message`` in a torn state. The lock is
    placed around *every* read and write so that callers always see a
    consistent (message, turn) pair — never a mix of old and new values.
    """

    def __init__(self) -> None:
        # Why not RLock: we never hold the lock across two method calls from
        # the same thread, so a plain Lock suffices and is marginally faster.
        self._lock = threading.Lock()
        self._message: str | None = None
        self._turn: int | None = None

    def send(self, text: str) -> dict:
        """Replace the stored message with *text*.

        Returns:
            ``{"success": True}`` always (errors propagate as exceptions).
        """
        with self._lock:
            self._message = text
            self._turn = None  # turn tracking delegated to orchestrator
            log.debug("MessageStore.send: stored %d chars.", len(text))
        return {"success": True}

    def receive(self) -> dict:
        """Return the latest stored message (nulls if nothing sent yet)."""
        with self._lock:
            msg = self._message
            turn = self._turn
        log.debug("MessageStore.receive: %r", msg)
        return {"message": msg, "turn": turn}

    def reset(self) -> None:
        """Clear the store — call between sub-games to avoid stale messages."""
        with self._lock:
            self._message = None
            self._turn = None
        log.debug("MessageStore reset.")
