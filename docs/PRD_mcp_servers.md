# PRD: MCP Servers Mechanism
**Version:** 1.00 | Part of: Cops & Robbers MCP Assignment

---

## 1. Description

Two FastMCP servers — one for the Cop agent and one for the Thief agent — act as the communication layer between agents. Each server exposes three tools. All reasoning happens in the MCP Client (Orchestrator), not inside the servers. Both servers require token-based authentication on every request and are deployed to Render (free tier) for the final submission.

---

## 2. Theoretical Background

The Model Context Protocol (MCP) is an open standard for connecting LLMs to external tools and resources. In this architecture, the MCP server is a pure interface layer: it exposes callable tools, validates inputs, and stores/retrieves messages. The LLM and all decision logic reside in the MCP Client. This separation follows the principle of least responsibility — the server knows nothing about the game state.

---

## 3. Tools Exposed (both servers)

### `validate_position(x: int, y: int) → dict`
Checks whether a cell is within board bounds and not blocked by a barrier.
```json
Request:  { "x": 3, "y": 2 }
Response: { "valid": true, "reason": null }
Response: { "valid": false, "reason": "barrier" }
Response: { "valid": false, "reason": "out_of_bounds" }
```

### `send_message(text: str) → dict`
Stores a free-form natural-language message from this agent, readable by the opponent on their next turn.
```json
Request:  { "text": "I'm closing in from the northwest." }
Response: { "success": true }
```

### `receive_message() → dict`
Retrieves the latest natural-language message sent by the opponent.
```json
Response: { "message": "You're running out of room.", "turn": 10 }
Response: { "message": null, "turn": null }
```

---

## 4. Authentication

Every request must include:
```
Authorization: Bearer <token>
```
- Token value is loaded from environment variable (`COP_MCP_TOKEN` / `THIEF_MCP_TOKEN`) on the server side
- FastMCP middleware validates the token before executing any tool
- Missing or invalid token → `401 Unauthorized`
- Token revocation: update the environment variable in Render dashboard and redeploy
- Tokens are never hardcoded or committed to the repository

---

## 5. Thread Safety

Both servers handle concurrent incoming requests. The message store (latest NL message per agent) is a shared resource and must be protected:
- Use `threading.Lock()` around all read/write operations on the message store
- Document why the lock is placed where it is in code comments
- Concurrent test must verify that two simultaneous `send_message` calls do not corrupt state

---

## 6. Inputs

| Input | Type | Source |
|-------|------|--------|
| `x`, `y` for position validation | `int` | MCP Client |
| `text` for NL message | `str` | MCP Client (from LLM) |
| Auth token | `str` (header) | MCP Client (from `.env`) |
| Board size and barrier locations (for validation) | Injected at server init | `config.json` |

---

## 7. Outputs

| Output | Type | Consumer |
|--------|------|----------|
| Position validity | `dict` | MCP Client |
| Message send confirmation | `dict` | MCP Client |
| Opponent's NL message | `dict` | MCP Client → LLM |
| `401 Unauthorized` | HTTP response | MCP Client (triggers error handling) |

---

## 8. Deployment

- **Local (development):** Cop server on `localhost:8001`; Thief server on `localhost:8002`
- **Cloud (submission):** Both deployed as Render Web Services (free tier); each gets a unique public HTTPS URL
- Render environment variables: `COP_MCP_TOKEN`, `THIEF_MCP_TOKEN` set in Render dashboard only
- Cold start latency: up to 60 seconds after 15 min of inactivity — acceptable during active gameplay

---

## 9. Performance Expectations

- Tool response time (local): < 5 ms
- Tool response time (Render, warm): < 500 ms including network round-trip
- Concurrent requests: server must handle at least 2 simultaneous requests without deadlock

---

## 10. Alternatives Considered

| Alternative | Reason rejected |
|-------------|----------------|
| Raw HTTP API (Flask/FastAPI) | Requires manual MCP protocol implementation; FastMCP handles this out of the box |
| Single shared server for both agents | Violates assignment architecture; must be two independent servers |
| No authentication | Render URLs are publicly reachable — unauthenticated servers are a security risk |
| IP allowlisting | Client IP may change between runs; token auth is simpler and more robust |

---

## 11. Success Criteria and Test Scenarios

| Scenario | Expected result |
|----------|----------------|
| Valid token + valid `validate_position` call | Returns `{ "valid": true/false }` correctly |
| Missing `Authorization` header | Returns `401 Unauthorized` |
| Invalid token value | Returns `401 Unauthorized` |
| `send_message` then `receive_message` | Opponent receives the exact text sent |
| Two concurrent `send_message` calls | Both succeed; no corruption; lock prevents race condition |
| Cop server called with Thief's token | Returns `401` (tokens are server-specific) |
