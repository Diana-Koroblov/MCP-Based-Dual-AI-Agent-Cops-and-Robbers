"""Token-based HTTP authentication middleware for FastMCP servers.

Why Starlette BaseHTTPMiddleware: FastMCP 2.x builds on Starlette, so wrapping
the ASGI app at the Starlette layer is the standard, transport-agnostic way to
add HTTP-level auth without touching tool logic.

Why here and not inside each tool function: keeping auth as a middleware layer
means tools stay pure and testable in isolation — you can call a tool function
in a unit test without providing an auth token.
"""

from __future__ import annotations

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

__all__ = ["TokenAuthMiddleware"]

log = logging.getLogger(__name__)


class TokenAuthMiddleware(BaseHTTPMiddleware):
    """Validates ``Authorization: Bearer <token>`` on every HTTP request.

    Missing or wrong token → 401 Unauthorized.  The token is compared with
    ``==`` (not a timing-safe comparison) which is acceptable for a class
    project where we are not defending against timing attacks.
    """

    def __init__(self, app, *, token: str) -> None:
        super().__init__(app)
        if not token:
            raise ValueError("Auth token must not be empty.")
        # Pre-build the expected header value once to avoid string allocation
        # on every request.
        self._expected = f"Bearer {token}"

    async def dispatch(self, request: Request, call_next):
        auth = request.headers.get("Authorization", "")
        if auth != self._expected:
            client = request.client.host if request.client else "unknown"
            log.warning(
                "Auth rejected from %s — header: %r",
                client,
                auth[:30] if auth else "(missing)",
            )
            return Response("Unauthorized", status_code=401)
        log.debug("Auth passed: %s %s", request.method, request.url.path)
        return await call_next(request)
