# Architecture & Planning Document (PLAN.md)
## Project: Cops & Robbers — Dual AI Agent Pursuit via MCP Servers
**Version:** 1.00  
**Last Updated:** 2026-06-24  

---

## 1. C4 Model — System Architecture

### Level 1: Context Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        External World                        │
│                                                              │
│   ┌──────────────┐        ┌──────────────────────────────┐  │
│   │  Lecturer    │        │      Cloud LLM Provider      │  │
│   │  (grader)    │        │  (Anthropic / OpenAI / etc.) │  │
│   └──────┬───────┘        └──────────────┬───────────────┘  │
│          │ receives email                │ API calls         │
│          ▼                               │                   │
│   ┌──────────────┐                       │                   │
│   │  Gmail API   │◄──────────────────────┤                   │
│   └──────────────┘     automated report  │                   │
│                                          │                   │
│          ┌───────────────────────────────▼─────────────┐    │
│          │         Cops & Robbers System               │    │
│          │  (Game Engine + MCP Clients + MCP Servers)  │    │
│          └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Level 2: Container Diagram

```
┌──────────────────── Local Machine ──────────────────────────┐
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                   Game Engine                        │    │
│  │  (Python process — orchestrates the full game loop) │    │
│  └───────┬──────────────────────────────────┬──────────┘    │
│          │                                  │               │
│  ┌───────▼──────────┐            ┌──────────▼───────────┐   │
│  │  Cop MCP Client  │            │ Thief MCP Client     │   │
│  │  (orchestrator)  │            │ (orchestrator)       │   │
│  └───────┬──────────┘            └──────────┬───────────┘   │
│          │ HTTPS                            │ HTTPS         │
└──────────┼──────────────────────────────────┼───────────────┘
           │                                  │
┌──────────▼──────── Cloud ───────────────────▼───────────────┐
│                                                              │
│  ┌─────────────────────┐     ┌──────────────────────────┐   │
│  │   Cop MCP Server    │     │   Thief MCP Server       │   │
│  │   (FastMCP)         │     │   (FastMCP)              │   │
│  │   Token auth        │     │   Token auth             │   │
│  └─────────────────────┘     └──────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

### Level 3: Component Diagram

```
src/
├── game/
│   ├── board.py            ← Grid class, cell access, boundary checks
│   ├── barriers.py         ← Barrier placement and validation
│   ├── movement.py         ← 8-direction movement, blocked cell checks
│   ├── turn_manager.py     ← Turn sequencing, move counter, win detection
│   ├── game_state.py       ← Immutable board snapshot
│   ├── sub_game.py         ← Single sub-game runner (25-move loop)
│   ├── full_game.py        ← 6 sub-game series orchestrator
│   └── scorer.py           ← Score calculation per result
│
├── mcp_servers/
│   ├── cop_server.py       ← FastMCP server (Cop), port 8001 locally
│   └── thief_server.py     ← FastMCP server (Thief), port 8002 locally
│
├── orchestrator/
│   ├── client.py           ← MCP client: connects to servers, invokes tools
│   ├── llm_loop.py         ← LLM query → tool call → result → repeat
│   ├── belief_state.py     ← Agent's internal estimate of opponent location
│   └── prompt_builder.py   ← Constructs system/user prompts per turn
│
├── strategy/
│   ├── heuristic_cop.py    ← Manhattan-distance pursuit logic
│   └── heuristic_thief.py  ← Evasion logic, maximize distance from cop
│
├── api_gateway/
│   └── gatekeeper.py       ← Rate limiting, FIFO queue, retry, logging
│
├── reporting/
│   ├── json_builder.py     ← Assembles the JSON report from game results
│   └── gmail_sender.py     ← Gmail API OAuth2 client, sends email
│
├── gui/
│   └── board_view.py       ← pygame board: grid, agents, barriers, scores, status
│
└── constants.py            ← Immutable project constants only
```

---

## 2. Data Flow — One Turn (Sequence)

```
Game Engine
    │
    ├─1─► prompt_builder  → builds NL prompt for active agent
    │
    ├─2─► llm_loop        → sends prompt to Cloud LLM API (via gatekeeper)
    │         │
    │         ◄── LLM responds with tool_call or text message
    │
    ├─3─► client.py       → invokes MCP tool on the agent's server
    │         │                (send_message / receive_message / validate_position)
    │         ◄── tool result returned
    │
    ├─4─► llm_loop        → feeds tool result back to LLM
    │         │
    │         ◄── LLM decides final action (move / place barrier)
    │
    ├─5─► game_state      → applies action, updates board
    │
    ├─6─► board_view      → re-renders GUI
    │
    └─7─► turn_manager    → checks win condition, advances turn counter
```

---

## 3. Deployment Diagram

### Stage 1 — Local (development)

```
Developer Machine
├── game engine (Python process)
├── cop_server.py     → localhost:8001
├── thief_server.py   → localhost:8002
└── Cloud LLM API     → outbound HTTPS only
```

### Stage 2 — Cloud (final submission)

```
Developer Machine
├── game engine (Python process)
├── Gemini API             → outbound HTTPS
├── Cop MCP Server URL     → outbound HTTPS  ──► Render: cop_server deployed
└── Thief MCP Server URL   → outbound HTTPS  ──► Render: thief_server deployed
```

**Recommended platform: Render (free tier)**
- No credit card required
- 750 free compute hours/month per service — more than enough for a student project
- Public HTTPS URL + managed TLS included automatically
- Services sleep after 15 min of inactivity (30–60 sec cold start) — not a problem during active gameplay since both servers receive continuous calls
- Each MCP server deploys as a separate Render Web Service
- Token-based authentication must be enforced on every request (see ADR-07)

Both servers must have public HTTPS URLs and must not be blocked by firewalls or institutional networks.

---

## 4. API Contracts

### 4.1 MCP Tools (both servers)

#### `validate_position(x: int, y: int) → dict`
Checks whether a cell is within bounds and not blocked by a barrier.

```json
Request:  { "x": 3, "y": 2 }
Response: { "valid": true, "reason": null }
Response: { "valid": false, "reason": "barrier" }
Response: { "valid": false, "reason": "out_of_bounds" }
```

#### `send_message(text: str) → dict`
Stores a natural-language message from this agent, readable by the opponent.

```json
Request:  { "text": "I'm closing in from the west." }
Response: { "success": true }
```

#### `receive_message() → dict`
Retrieves the latest natural-language message sent by the opponent.

```json
Response: { "message": "I could be anywhere in the lower half by now.", "turn": 10 }
Response: { "message": null, "turn": null }
```

### 4.2 Authentication Header (all requests)

```
Authorization: Bearer <MCP_TOKEN>
```

Token loaded from environment variable. Never hardcoded.

### 4.3 LLM API (via Gatekeeper)

All LLM calls go through `gatekeeper.py`. The gatekeeper wraps the provider SDK (Anthropic / OpenAI) and enforces rate limits from `config/rate_limits.json`.

---

## 5. Data Schemas

### 5.1 Game State (internal)

```python
@dataclass(frozen=True)
class GameState:
    cop_pos: tuple[int, int]
    thief_pos: tuple[int, int]
    barriers: frozenset[tuple[int, int]]
    move_count: int
    barriers_placed: int       # cop only, resets each sub-game
    active_player: str         # "cop" | "thief"
```

### 5.2 Sub-Game Result

```python
@dataclass
class SubGameResult:
    sub_game_index: int        # 1–6
    winner: str                # "cop" | "thief" | "technical_failure"
    moves: int
    cop_score: int
    thief_score: int
    barriers_placed: int
    final_state: GameState
```

### 5.3 JSON Report — Internal Game

```json
{
  "group_name": "Team-Name",
  "students": [
    { "name": "Student A", "id": "123456789" }
  ],
  "github_repo": "https://github.com/team/repo",
  "cop_mcp_url": "https://cop.example.com",
  "thief_mcp_url": "https://thief.example.com",
  "timezone": "Asia/Jerusalem",
  "sub_games": [
    {
      "index": 1,
      "winner": "cop",
      "moves": 14,
      "cop_score": 20,
      "thief_score": 5
    }
  ],
  "totals": {
    "cop": 90,
    "thief": 40
  }
}
```

### 5.4 Config Schema (`config/config.json`)

```json
{
  "version": "1.00",
  "grid_size": [5, 5],
  "max_moves": 25,
  "num_games": 6,
  "max_barriers": 5,
  "cop_mcp_url": "http://localhost:8001",
  "thief_mcp_url": "http://localhost:8002",
  "llm_provider": "gemini",
  "report_email": "rmisegal+uoh26b@gmail.com",
  "scoring": {
    "cop_win": 20,
    "thief_win": 10,
    "cop_loss": 5,
    "thief_loss": 5
  }
}
```

### 5.5 Rate Limits Schema (`config/rate_limits.json`)

```json
{
  "rate_limits": {
    "version": "1.00",
    "services": {
      "default": {
        "requests_per_minute": 30,
        "requests_per_hour": 500,
        "concurrent_max": 5,
        "retry_after_seconds": 30,
        "max_retries": 3
      }
    }
  }
}
```

---

## 6. GUI Design

**Technology:** pygame  
**Style:** simple and clean — flat colored cells, no gradients

### Layout

```
┌──────────────────────────────────┬─────────────────────┐
│                                  │  Scores             │
│          5×5 Board               │  Cop:   45          │
│                                  │  Thief: 20          │
│  [ ][ ][X][ ][ ]                 ├─────────────────────┤
│  [ ][C][ ][ ][X]                 │  Status             │
│  [ ][ ][ ][T][ ]                 │  Sub-game: 3 / 6    │
│  [ ][ ][ ][ ][ ]                 │  Move:     11 / 25  │
│  [ ][X][ ][ ][ ]                 │  Turn:     Thief    │
│                                  │  Barriers: ██░░░    │
└──────────────────────────────────┴─────────────────────┘
```

**Legend:** C = Cop (blue), T = Thief (orange), X = Barrier (dashed)

### Cell colors
| State | Fill | Border |
|-------|------|--------|
| Empty | `--color-background-secondary` | light |
| Cop | `#B5D4F4` | `#378ADD` |
| Thief | `#F5C4B3` | `#D85A30` |
| Barrier | dark gray, dashed | medium |

### File: `src/gui/board_view.py`
- Max 150 lines of code — split into `board_renderer.py` and `sidebar_renderer.py` if needed
- No business logic — reads from `GameState` only, never modifies it
- Updates on every turn via a callback from `full_game.py`

---

## 7. Architectural Decision Records (ADRs)

### ADR-01: FastMCP for MCP Servers

**Decision:** Use FastMCP to implement both MCP servers.  
**Rationale:** FastMCP is the standard Python library for building MCP-compliant servers. It handles tool registration, schema generation, and protocol compliance out of the box.  
**Trade-off:** Less control over low-level protocol details, but significantly less boilerplate.  
**Alternatives considered:** Raw HTTP server (Flask/FastAPI) — rejected because it requires manual MCP protocol implementation.

### ADR-02: Gemini API for LLM

**Decision:** Use Google Gemini API for agent reasoning.  
**Rationale:** Stable cloud deployment, no firewall complications, no local hardware exposure. Gemini offers a generous free tier (Gemini 1.5 Flash) suitable for the short interactions in this project — 6 sub-games of up to 25 moves each will stay well within free limits.  
**Trade-off:** Requires a `GEMINI_API_KEY` from Google AI Studio (free). Response quality and tool-calling behavior may differ slightly from other providers.  
**Alternatives considered:** Anthropic / OpenAI — both valid but require paid tiers sooner; Local Ollama — rejected due to networking complexity.

### ADR-03: Hybrid Architecture as Fallback

**Decision:** If cloud API quota runs out, switch to Hybrid — local Ollama for inference, cloud-only for MCP servers.  
**Rationale:** Outbound HTTPS from local machine to cloud MCP servers requires no inbound firewall ports, keeping the local machine secure while MCP servers remain publicly reachable.  
**Trade-off:** Requires Ollama installed locally; model quality may differ from cloud LLMs.

### ADR-04: Heuristic Strategy (No RL)

**Decision:** Implement decision-making via Manhattan-distance heuristics, not Q-Learning.  
**Rationale:** RL is explicitly optional per the assignment. The grading focus is on orchestration and communication, not game-playing quality. Heuristics are faster to implement, easier to test, and sufficient to demonstrate a working system.  
**Trade-off:** Agents will not improve over time. If time permits, Q-table can be added as an extension.  
**Alternatives considered:** Tabular Q-Learning — documented in `docs/PRD_strategy.md` as an optional extension.

### ADR-05: Centralized API Gatekeeper

**Decision:** All external API calls (LLM, Gmail) must pass through `src/api_gateway/gatekeeper.py`.  
**Rationale:** Required by the submission guidelines. Provides centralized rate limiting, retry logic, and logging.  
**Trade-off:** Adds one layer of indirection to every API call.

### ADR-07: Render for Cloud Deployment

**Decision:** Deploy both MCP servers to Render (free tier).  
**Rationale:** Only platform among the assignment's suggestions that is genuinely free — no credit card required, 750 hours/month per service, automatic HTTPS with managed TLS. Railway requires $1/month minimum; Prefect Cloud is designed for workflow orchestration, not persistent HTTP servers.  
**Trade-off:** Services sleep after 15 minutes of inactivity (30–60 sec cold start). Acceptable for this project since servers receive continuous calls during gameplay.  
**Alternatives considered:** Railway ($1/month after trial), Prefect Cloud (wrong tool category).

### ADR-08: Token-Based Authentication on MCP Servers

**Decision:** All requests to both MCP servers must include a `Authorization: Bearer <token>` header. Token values are loaded from environment variables on the server side and injected by the MCP client from its own `.env`.  
**Rationale:** Public HTTPS endpoints on Render are reachable by anyone. Without auth, any party can send arbitrary tool calls to the servers.  
**Trade-off:** Adds a small amount of configuration overhead. Token rotation requires redeployment.  
**Alternatives considered:** IP allowlisting — not feasible since the client IP may change; No auth — explicitly forbidden by the assignment.

### ADR-09: pygame for GUI

**Decision:** Use pygame for the game board visualization.  
**Rationale:** Good balance between visual quality and implementation simplicity. Supports real-time rendering per turn. Tkinter is simpler but produces a less polished result.  
**Trade-off:** Requires `uv add pygame`; slightly more setup than tkinter.

### ADR-10: Gmail API over SMTP

**Decision:** Use Gmail API with OAuth2 (`token.json`) instead of SMTP with username/password.  
**Rationale:** Required by the assignment and the instructor's guidance. OAuth tokens have limited scope and lifetime and can be revoked, unlike stored passwords.  
**Trade-off:** Requires one-time browser-based OAuth flow to generate `token.json`.

---

## 8. Security Architecture

| Concern | Solution |
|---------|----------|
| MCP server authentication | Bearer token per request, loaded from env var |
| LLM API key | Environment variable only, never in source |
| Gmail credentials (`my_google.json`) | Stored outside project directory in `~/private_google/` |
| Gmail token (`token.json`) | Same private folder, auto-refreshed by Google client |
| Secrets in repo | `.gitignore` covers `.env`, `*.json` credentials, `*.pem`, `*.key` |
| Token revocation | Supported by both MCP token system and Google OAuth |

---

## 9. Project Folder Structure

```
project-root/
├── src/
│   ├── game/
│   │   ├── __init__.py
│   │   ├── board.py
│   │   ├── barriers.py
│   │   ├── movement.py
│   │   ├── turn_manager.py
│   │   ├── game_state.py
│   │   ├── sub_game.py
│   │   ├── full_game.py
│   │   └── scorer.py
│   ├── mcp_servers/
│   │   ├── __init__.py
│   │   ├── cop_server.py
│   │   └── thief_server.py
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   ├── llm_loop.py
│   │   ├── belief_state.py
│   │   └── prompt_builder.py
│   ├── strategy/
│   │   ├── __init__.py
│   │   ├── heuristic_cop.py
│   │   └── heuristic_thief.py
│   ├── api_gateway/
│   │   ├── __init__.py
│   │   └── gatekeeper.py
│   ├── reporting/
│   │   ├── __init__.py
│   │   ├── json_builder.py
│   │   └── gmail_sender.py
│   ├── gui/
│   │   ├── __init__.py
│   │   └── board_view.py
│   └── constants.py
├── tests/
│   ├── conftest.py
│   ├── test_board.py
│   ├── test_barriers.py
│   ├── test_movement.py
│   ├── test_turn_manager.py
│   ├── test_scorer.py
│   ├── test_sub_game.py
│   ├── test_cop_server.py
│   ├── test_thief_server.py
│   ├── test_client.py
│   ├── test_llm_loop.py
│   ├── test_belief_state.py
│   ├── test_prompt_builder.py
│   ├── test_gatekeeper.py
│   ├── test_json_builder.py
│   ├── test_gmail_sender.py
│   └── test_file_size.py
├── docs/
│   ├── PRD.md
│   ├── PLAN.md
│   ├── TODO.md
│   ├── PRD_game_engine.md
│   ├── PRD_mcp_servers.md
│   ├── PRD_nlp_communication.md
│   ├── PRD_strategy.md
│   └── PRD_reporting.md
├── config/
│   ├── config.json
│   └── rate_limits.json
├── assets/
│   └── screenshots/
├── results/
├── notebooks/
│   └── results_analysis.ipynb
├── README.md
├── pyproject.toml
├── uv.lock
├── .env-example
└── .gitignore
```

---

## 10. pyproject.toml Template

```toml
[project]
name = "cops-robbers-mcp"
version = "1.0.0"
description = "Dual AI agent pursuit game via MCP servers"
requires-python = ">=3.10"
dependencies = [
    "fastmcp",
    "google-generativeai",
    "google-api-python-client",
    "google-auth-httplib2",
    "google-auth-oauthlib",
    "pygame",
    "python-dotenv",
    "httpx",
]

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "SIM"]
ignore = ["E501"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=src --cov-report=term-missing --cov-fail-under=85"

[tool.coverage.run]
branch = true
source = ["src"]
```

---

## 11. Environment Variables (`.env-example`)

```
# Gemini API (get free key at https://aistudio.google.com/)
GEMINI_API_KEY=your_gemini_api_key_here

# MCP Server tokens
COP_MCP_TOKEN=your_cop_token_here
THIEF_MCP_TOKEN=your_thief_token_here

# Gmail API (paths outside project directory)
GMAIL_CREDENTIALS_PATH=/path/to/private_google/my_google.json
GMAIL_TOKEN_PATH=/path/to/private_google/token.json
REPORT_RECIPIENT=rmisegal+uoh26b@gmail.com
```
