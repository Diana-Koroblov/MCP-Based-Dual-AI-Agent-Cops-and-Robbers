# Work Plan — Cops & Robbers MCP Agent Assignment

---

## Project Overview

Build a fully autonomous Cops-and-Robbers pursuit game where two AI agents (Cop and Thief) communicate through MCP servers using free-form natural language on a 5×5 grid. The system must run 6 sub-games end-to-end without manual intervention and send an automated JSON report by email.

---

## Phase 1 — Documentation (before any code)

> Per the submission guidelines, all documentation must be approved before development starts.

### 1.1 `docs/PRD.md`
- Project purpose, user problem, goals
- Functional requirements: game rules, MCP communication, LLM integration, email reporting
- Non-functional requirements: security (token auth), configurability (no hardcoded values), 85% test coverage, zero Ruff violations
- Acceptance criteria: 6 valid sub-games complete autonomously, email received with valid JSON, both MCP servers publicly reachable
- KPIs: sub-game success rate, average moves per game, cop win rate
- Milestones aligned with phases below

### 1.2 `docs/PLAN.md`
- System architecture using the C4 Model (Context → Container → Component)
- Component diagram: Game Engine, SDK layer, MCP Client (Orchestrator), Cop MCP Server, Thief MCP Server, Gemini API, Gmail API
- Deployment diagram: local (dev) → cloud on Render (submission)
- Data flow: game engine → LLM → tool call → MCP server → response → LLM → next move
- API contracts: MCP tool definitions (`validate_position`, `send_message`, `receive_message`), SDK public interface
- Architectural Decision Records (ADRs): FastMCP, Gemini API, Render, token auth, heuristic strategy, SDK design
- Data schemas: game state, observed state (fog of war), sub-game result, JSON report
- Extensibility design: plugin architecture, extension interfaces, middleware hooks for future consumers
- **ISO/IEC 25010 alignment**: document how the system addresses each quality dimension — functional suitability, performance efficiency, reliability, security, maintainability, portability

### 1.3 `docs/TODO.md`
- Phased task table with ID, description, priority, status, assignee, Definition of Done
- Must be updated continuously throughout development

### 1.4 Dedicated PRDs for major mechanisms
- `docs/PRD_game_engine.md` — grid, movement, barriers, fog of war, turn logic, win conditions
- `docs/PRD_mcp_servers.md` — FastMCP setup, tools exposed, token authentication
- `docs/PRD_nlp_communication.md` — NL message format, prompt design, NLP parsing, belief updating
- `docs/PRD_strategy.md` — heuristic/Manhattan distance decision-making
- `docs/PRD_reporting.md` — Gmail API OAuth flow, JSON report schema, email trigger logic

---

## Phase 2 — Project Scaffolding

### 2.1 Repository & Package Setup
- Initialize Git repo with `.gitignore` (include `.env`, `.pem`, `.key`, credentials)
- Create `.env-example` with placeholder values for: `GEMINI_API_KEY`, `GMAIL_CREDENTIALS_PATH`, `COP_MCP_TOKEN`, `THIEF_MCP_TOKEN`
- Set up `pyproject.toml` as single source of truth (name, version `1.0.0`, dependencies)
- Create `src/version.py` containing `VERSION = "1.00"` — version must match `pyproject.toml` and all `config/*.json` files
- Configure Ruff in `pyproject.toml`:
  ```toml
  [tool.ruff]
  line-length = 100
  target-version = "py310"
  [tool.ruff.lint]
  select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "SIM"]
  ignore = ["E501"]
  ```
- Run `uv sync` (never `pip install`), commit `uv.lock`

### 2.2 Git Workflow (maintained throughout development)
- One feature branch per phase (e.g., `phase/3-game-engine`, `phase/4-mcp-servers`)
- Pull request + self-review before merging each branch to `main`
- Meaningful commit messages: `feat: add fog-of-war filter`, `fix: barrier overwrite rejected`, `test: sanity check 3x3`
- Tag each completed milestone: `git tag M3-game-engine`, `M5-local-pipeline`, etc.
- Keep history clean — no merge commits with auto-generated messages

### 2.3 CI/CD Pipeline (GitHub Actions)
Create `.github/workflows/ci.yml` that triggers on every push and pull request:
```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync
      - run: uv run ruff check src/ tests/
      - run: uv run pytest tests/ --cov=src --cov-fail-under=85
```
- Direct calls to `pytest` or `python -m pytest` are forbidden in CI
- Pipeline must pass before any branch is merged to `main`

### 2.2 Folder Structure
```
project-root/
├── src/
│   ├── sdk/            # PUBLIC SDK — single entry point for all consumers
│   │   ├── __init__.py     # exposes __all__ public interface
│   │   └── game_sdk.py     # SDK facade: wraps all business logic modules
│   ├── game/           # core game logic
│   │   └── __init__.py
│   ├── mcp_servers/    # cop and thief MCP servers
│   │   └── __init__.py
│   ├── orchestrator/   # MCP client + LLM loop
│   │   └── __init__.py
│   ├── strategy/       # decision-making logic
│   │   └── __init__.py
│   ├── reporting/      # Gmail API, JSON builder
│   │   └── __init__.py
│   ├── api_gateway/    # central API gatekeeper
│   │   └── __init__.py
│   ├── gui/            # pygame board visualization — uses SDK only
│   │   └── __init__.py
│   └── constants.py    # immutable constants only
├── tests/
│   └── conftest.py     # shared fixtures for all test files
├── docs/
├── config/
│   ├── config.json
│   └── rate_limits.json
├── assets/             # GUI screenshots, diagrams
├── results/            # game outputs, logs
├── notebooks/          # results analysis notebook
├── README.md
├── pyproject.toml
├── uv.lock
├── .env-example
└── .gitignore
```

### 2.3 Package Structure Rules (mandatory)
- Every `src/` subdirectory must contain `__init__.py` to be a proper Python package
- Each `__init__.py` must define `__all__` to explicitly declare the public interface of that package
- All imports across the codebase must use **relative or package-based paths only**
- Absolute filesystem paths in imports are strictly forbidden (e.g., `sys.path.append(...)` is banned)
- File read/write operations must also use package-aware paths, not hard-coded OS paths

```python
# Correct — relative import
from .board import Board
from ..constants import MAX_BARRIERS

# Correct — package import
from src.game.board import Board

# FORBIDDEN — absolute filesystem path
import sys; sys.path.append("/home/user/project/src")
```

### 2.5 Config Validation at Startup
Add a `config_validator.py` that runs at application startup:
- Loads `config/config.json` and checks the `version` field matches the expected version in `src/version.py`
- Loads `config/rate_limits.json` and validates required keys exist
- Raises a clear `ConfigVersionError` with a human-readable message if versions are mismatched
- All other modules must call the validator before reading config values

### 2.6 SDK Layer (`src/sdk/`)

The SDK is the **single entry point** for all business logic. No external consumer — GUI, CLI, tests, or future integrations — may import from `src/game/`, `src/orchestrator/`, `src/reporting/`, etc. directly. They must go through the SDK.

```python
# src/sdk/__init__.py
__all__ = ["GameSDK"]

# src/sdk/game_sdk.py
class GameSDK:
    """Central facade for all game operations.

    Why: enforces separation between business logic and consumers.
    The GUI, CLI, and any future interface all go through here,
    so internal modules can be refactored without touching consumers.
    """
    def start_game(self) -> None: ...
    def get_observed_state(self, agent: str) -> ObservedState: ...
    def submit_action(self, agent: str, action: Action) -> GameState: ...
    def get_scores(self) -> ScoreSummary: ...
    def send_report(self) -> bool: ...
```

Rules:
- **GUI** calls `sdk.get_observed_state()` and `sdk.submit_action()` — never imports from `src/game/` directly
- **Reporting** is triggered via `sdk.send_report()` — not called directly by `full_game.py`
- **Tests** may import internal modules directly (they are not consumers in the SDK sense — they test units)
- Business logic must be completely separated from infrastructure (files, external APIs)

### 2.7 `config/config.json`
```json
{
  "version": "1.00",
  "grid_size": [5, 5],
  "max_moves": 25,
  "num_games": 6,
  "max_barriers": 5,
  "visibility_radius": 2,
  "cop_mcp_url": "http://localhost:8001",
  "thief_mcp_url": "http://localhost:8002",
  "llm_provider": "gemini",
  "scoring": {
    "cop_win": 20,
    "thief_win": 10,
    "cop_loss": 5,
    "thief_loss": 5
  },
  "report_email": "rmisegal+uoh26b@gmail.com"
}
```

### 2.8 `config/rate_limits.json`
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

### 2.9 `.env-example`
```
GEMINI_API_KEY=your_gemini_api_key_here
COP_MCP_TOKEN=your_cop_token_here
THIEF_MCP_TOKEN=your_thief_token_here
GMAIL_CREDENTIALS_PATH=/path/to/private_google/my_google.json
GMAIL_TOKEN_PATH=/path/to/private_google/token.json
REPORT_RECIPIENT=rmisegal+uoh26b@gmail.com
```

---

## Phase 3 — Core Game Engine (`src/game/`)

> File size limit: max 150 lines of code per file. Split as needed.

### 3.1 Files
- `board.py` — Grid class: initialization, cell access, boundary checks, configurable size
- `barriers.py` — Barrier placement and validation (hard limit: exactly 5 per cop per sub-game)
- `movement.py` — Move validation (8 directions + diagonal), blocked cell checks
- `fog_of_war.py` — **Partial Observability filter** — masks opponent position before state is passed to agents
- `turn_manager.py` — Turn sequencing (Thief first → Cop), move counter, win detection
- `game_state.py` — Full internal board state (cop pos, thief pos, barriers, turn count)
- `observed_state.py` — Agent-facing masked state (own position only + known barriers + fog)
- `sub_game.py` — Single sub-game runner (25-move loop, termination conditions)
- `full_game.py` — **Continuous 6 sub-game loop** — runs all sub-games automatically, no manual intervention
- `scorer.py` — Score calculation per sub-game + **cumulative totals** across all 6 games

### 3.2 Key rules to enforce
- Cop wins: cop cell == thief cell → capture
- Thief wins: survives all 25 moves without capture
- Barrier: placed at cop's **current** cell; cop does not move that turn; cell becomes permanently impassable for both agents for the remainder of that sub-game; cannot be overwritten by a second barrier
- **Hard barrier limit: exactly 5 per Cop per sub-game** — any attempt beyond 5 must be rejected by `barriers.py` and treated as an invalid move
- Technical failure → sub-game is invalid, automatically rerun until a valid result is produced
- Barriers reset between sub-games; positions reset to initial (random or configured)

### 3.3 Partial Observability — Fog of War (`fog_of_war.py`)

**This is a core requirement.** The engine must never expose the opponent's true position directly to an agent.

```python
@dataclass(frozen=True)
class ObservedState:
    own_pos: tuple[int, int]
    known_barriers: frozenset[tuple[int, int]]
    opponent_visible: bool          # True only if within visibility_radius
    opponent_pos_if_visible: tuple[int, int] | None
    move_count: int
    barriers_remaining: int         # cop only
```

Rules:
- Each agent receives only `ObservedState`, never the full `GameState`
- The opponent's position is revealed only if it falls within `visibility_radius` cells (configurable, default 2)
- Outside that radius, `opponent_visible = False` and `opponent_pos_if_visible = None`
- The agent must infer the opponent's probable location from NL messages and partial observations

### 3.4 Code Comment Standards (applies to all `src/` files)

Comments must explain **why**, not just what. Required for:
- Every non-obvious design choice (e.g., why visibility radius defaults to 2 and not 1)
- Every assumption (e.g., "we assume Thief always moves first per assignment rules")
- Every edge case handled (e.g., "barrier on cop's starting cell is valid on turn 1")

```python
# WHY: the barrier is placed on the cop's current cell, not a target cell.
# This ensures the cop cannot trap itself by blocking its own starting position
# across multiple turns — the cell becomes impassable immediately after placement.
def place_barrier(self, state: GameState) -> GameState:
    ...
```

### 3.5 Mixin Pattern for File Size Compliance

When any class in `src/game/` approaches 150 lines, split responsibilities using Mixins. Each mixin handles exactly one concern and must be independently testable.

Example split for `sub_game.py` if it grows large:
```
sub_game.py             ← main SubGame class (composes mixins)
sub_game_validator.py   ← SubGameValidatorMixin (win detection, move legality)
sub_game_logger.py      ← SubGameLoggerMixin (turn logging, event recording)
```

Mixin rules:
- Small and focused — one responsibility per mixin
- No mixin should override another mixin's methods unexpectedly
- Each mixin must have its own test file

### 3.6 Edge Cases, Logging & Defensive Programming (all `src/game/` files)
- Every function must validate its inputs before use (e.g., reject move outside grid bounds with a clear error, not a crash)
- Use Python's `logging` module — not `print()` — with level, timestamp, and context on every significant event
- Edge cases must be commented inline and covered by dedicated tests:
  - Barrier placed on cop's starting cell on turn 1
  - Cop attempts a 6th barrier (must be rejected)
  - Both agents start on the same cell (must be handled)
  - Technical failure mid-sub-game (triggers rerun)
- Graceful degradation: if a single LLM call fails, retry via gatekeeper before propagating the error

### 3.7 Continuous Full Game Loop (`full_game.py`)
- Calls `sub_game.run()` in sequence, 6 times
- On technical failure: reruns that sub-game automatically
- After each sub-game: passes result to `scorer.py`, accumulates totals
- After sub-game 6: triggers the reporting module automatically
- No user input required at any point during the loop

---

## Phase 4 — MCP Server Infrastructure (`src/mcp_servers/`)

### 4.1 Two FastMCP servers
- `cop_server.py` — MCP server for the Cop agent (port 8001 locally)
- `thief_server.py` — MCP server for the Thief agent (port 8002 locally)

### 4.2 Tools each server must expose
- `validate_position(x, y)` — checks if a position is within bounds and not blocked
- `send_message(text)` — stores a natural-language message from this agent
- `receive_message()` — retrieves the latest NL message from the opponent

### 4.3 Thread Safety
Both MCP servers handle concurrent incoming requests. Shared state must be protected:
- Message store (latest NL message per agent) must use a `threading.Lock()` or `threading.RLock()`
- Any shared counter or game-state reference must be accessed atomically
- Document thread-safety choices in code comments explaining why each lock is placed where it is

### 4.4 Token-Based Authentication — Mandatory

**Every request to both servers must include a valid bearer token.** This applies both locally and in cloud deployment.

```
Authorization: Bearer <token>
```

Implementation requirements:
- Token value is loaded from an environment variable on the **server** side (`COP_MCP_TOKEN` / `THIEF_MCP_TOKEN`)
- FastMCP middleware validates the token on every incoming request before executing any tool
- Requests with missing or invalid tokens receive `401 Unauthorized`
- Tokens are injected by the MCP client from its own `.env` — never hardcoded
- Support token revocation by updating the environment variable and redeploying

### 4.5 Architecture rule
- The LLM is NOT inside the MCP server
- Servers expose tools only; all reasoning happens in the MCP Client (Orchestrator)

---

## Phase 5 — MCP Client / Orchestrator (`src/orchestrator/`)

### 5.1 Files
- `client.py` — MCP client: connects to both servers, injects auth token, manages tool calls
- `llm_loop.py` — LLM interaction loop: send prompt → get response → detect tool call → invoke tool → feed result back
- `belief_state.py` — Agent's internal probabilistic estimate of opponent location, updated each turn
- `prompt_builder.py` — Constructs prompts: role, `ObservedState`, received NL message, allowed actions
- `nlp_parser.py` — **NLP parsing**: extracts agent intentions from free-form text and maps them to tool calls

### 5.2 LLM: Gemini API
- Use `google-generativeai` SDK with `GEMINI_API_KEY` from environment variable
- Key never hardcoded
- All API calls routed through the API Gatekeeper

### 5.3 Free-Form Natural Language Communication — Strict Requirement

**Agents must never transmit raw coordinates.** Sending `"I am at (3,2)"` or `"move to (4,1)"` is a protocol violation.

Required message style:
- `"I'm closing in from the northwest — you're running out of room."`
- `"I just blocked the eastern corridor. Your escape route is shrinking."`
- `"I sense you're somewhere in the lower half of the board."`

Deception is permitted and must be handled by the receiving agent.

### 5.4 NLP Parsing (`nlp_parser.py`)

The Orchestrator must not pass raw LLM text directly to tool calls. Instead, `nlp_parser.py` is responsible for:

1. Receiving the agent's natural-language output
2. Extracting the **intended action** (move direction, barrier placement, or hold)
3. Translating the intention into a concrete tool invocation (`validate_position`, `send_message`)
4. Updating `belief_state.py` with any spatial inferences from the message

```python
# Example flow
raw_text = "I'm heading northeast to cut off your escape."
intention = nlp_parser.extract_intention(raw_text)
# → IntentionResult(action="move", direction="northeast", confidence=0.9)
target_cell = intention.resolve_on_board(current_pos, board_size)
client.validate_position(target_cell.x, target_cell.y)
```

### 5.5 Belief State Updates
- After receiving an opponent's NL message, `belief_state.py` maintains a probability distribution over opponent cells
- Updated each turn using: direct observation (if within visibility radius) + NL inference + prior position
- The strategy module reads from `belief_state` to make movement decisions

---

## Phase 6 — Strategy (`src/strategy/`)

### 6.1 Heuristic (Manhattan distance)
- `heuristic_cop.py` — moves toward highest-probability thief cell from `belief_state`; places barriers to cut off likely escape routes
- `heuristic_thief.py` — moves away from highest-probability cop cell; maximizes estimated distance

### 6.2 Optional: Q-Table (if time permits)
- `q_table.py` — state/action table with Bellman update, epsilon-greedy policy
- State: (`own_pos`, `estimated_opponent_pos`, `barriers_tuple`)
- Actions: 8 directions + `place_barrier` (cop only)

---

## Phase 7 — API Gatekeeper (`src/api_gateway/`)

- `gatekeeper.py` — central entry point for ALL external API calls (Gemini, Gmail)
- Enforces rate limits from `config/rate_limits.json`
- FIFO queue with configurable maximum depth; backpressure when queue is full; drain mechanism when rate window resets
- Retry logic with configurable delay and max retries
- Logs every API call: provider, input tokens, output tokens, estimated cost, latency, success/fail
- Queue and rate-limit counters must be thread-safe
- Direct API calls bypassing the gatekeeper are forbidden

---

## Phase 8 — GUI (`src/gui/`)

**Technology:** pygame  
**Style:** simple and clean — flat colored cells, no gradients

### 8.1 Technical implementation
- `board_view.py` — renders the 5×5 grid, cop/thief positions, barriers, scores, status panel
- Shows: grid, cop (blue), thief (orange), barriers (dashed), sub-game number, move counter, turn indicator, barriers remaining (pip display), cumulative scores
- No message log (not required)
- GUI communicates **only through the SDK** — `sdk.get_observed_state()`, `sdk.get_scores()` — never imports game modules directly
- Updates on every turn via callback registered through the SDK

### 8.2 UI/UX Evaluation — Nielsen's Heuristics

The interface must be evaluated against the following usability criteria before submission. Document each in the README:

| Heuristic | How it applies to this GUI |
|-----------|---------------------------|
| Visibility of system status | Move counter, sub-game number, and whose turn it is are always visible |
| Match between system and real world | Grid coordinates displayed in familiar (x,y) format; cop/thief icons are intuitive |
| User control and freedom | Game can be paused or exited cleanly at any point without data corruption |
| Consistency and standards | Colors are consistent throughout (blue = cop, orange = thief, dashed = barrier) |
| Error prevention | Invalid states (e.g., barrier on occupied cell) are blocked by engine — GUI never shows them |
| Recognition rather than recall | All game state visible at a glance — no hidden menus or memory required |
| Flexibility and efficiency | Grid size configurable via config — no code change needed for different board sizes |
| Aesthetic and minimalist design | Only essential information shown — no clutter |
| Help users recover from errors | Technical failure displays a clear "sub-game failed, rerunning…" message |

### 8.3 Interface Documentation (required for README)
- Screenshot of each distinct GUI state: game start, mid-game with barriers, capture moment, sub-game end screen, series complete screen
- Description of the typical workflow a viewer observes when watching the game run
- Accessibility note: color choices must be distinguishable; key information also conveyed via text labels, not color alone

---

## Phase 9 — Cloud Deployment on Render

### 9.1 Platform: Render (free tier)
- **No credit card required**
- 750 free compute hours/month per service — sufficient for a student project
- Automatic public HTTPS URL + managed TLS
- Services sleep after 15 min of inactivity (30–60 sec cold start on first call, not a problem during active gameplay)

### 9.2 Deploy both MCP servers
- Deploy `cop_server.py` as one Render Web Service
- Deploy `thief_server.py` as a second Render Web Service
- Each gets a unique public URL (e.g., `https://cop-mcp-xxx.onrender.com`)

### 9.3 Token Authentication on Render
- Set `COP_MCP_TOKEN` and `THIEF_MCP_TOKEN` as **environment variables in Render's dashboard** — never in source code or committed files
- The FastMCP middleware reads the token from the environment and validates every incoming request
- Requests without a valid token receive `401 Unauthorized`

### 9.4 Update config
- Replace `cop_mcp_url` and `thief_mcp_url` in `config.json` with the live Render URLs
- Run a full end-to-end test with cloud servers before final submission

### 9.5 Networking
- Local game engine makes outbound HTTPS requests to Render — no inbound ports needed on local machine
- Do not deploy or test from a workplace/institutional network

---

## Phase 10 — Automated Reporting (`src/reporting/`)

### 10.1 Gmail API setup
- Use Google OAuth2 (not SMTP) — credentials in `my_google.json` stored outside the project directory
- `token.json` auto-generated on first run (browser popup), stored in same private folder
- Paths loaded from `.env`, never hardcoded

### 10.2 JSON report (internal game)
```json
{
  "group_name": "Team-Name",
  "students": [{"name": "Student A", "id": "123456789"}],
  "github_repo": "https://github.com/team/repo",
  "cop_mcp_url": "https://cop-mcp-xxx.onrender.com",
  "thief_mcp_url": "https://thief-mcp-xxx.onrender.com",
  "timezone": "Asia/Jerusalem",
  "sub_games": [
    {"index": 1, "winner": "cop", "moves": 14, "cop_score": 20, "thief_score": 5}
  ],
  "totals": {"cop": 90, "thief": 40}
}
```

### 10.3 Rules
- Email body contains **only** the JSON — no free-form text
- Send to: `rmisegal+uoh26b@gmail.com`
- Triggered automatically by `full_game.py` after sub-game 6 completes
- Technical failures trigger sub-game rerun — the report is only sent after 6 **valid** results

---

## Phase 11 — Testing (`tests/`)

> Follow TDD: Red → Green → Refactor. Write tests before or alongside implementation.

### 11.1 Standard coverage requirements (mandatory)
- At least **85% global coverage** (statement + branch)
- Every module has a matching test file
- Every public function must have **at minimum two tests**: one for the normal (happy) path and one for the failure path
- External dependencies (Gemini API, Gmail, MCP servers) must be mocked — tests must not call live services
- Test files obey the 150-line limit
- `test_file_size.py` — scans `src/`, fails if any file exceeds 150 code lines

### 11.2 `conftest.py` — Shared Fixtures (mandatory)

All fixtures shared across multiple test files must be placed in `tests/conftest.py`. Duplicating fixtures across test files is forbidden.

Required fixtures to define in `conftest.py`:
```python
@pytest.fixture
def default_config() -> dict: ...          # loads config.json with 5x5 defaults

@pytest.fixture
def small_config() -> dict: ...            # 2x2 config for sanity checks

@pytest.fixture
def initial_game_state() -> GameState: ... # cop at (0,0), thief at (4,4), no barriers

@pytest.fixture
def mock_gemini_client() -> MagicMock: ... # mocked LLM responses

@pytest.fixture
def mock_mcp_client() -> MagicMock: ...    # mocked MCP tool calls

@pytest.fixture
def mock_gmail_sender() -> MagicMock: ...  # mocked email sending
```

### 11.3 Progressive Sanity Checks (integration testing by grid size)

> **On your question:** keep both. The sanity checks do not replace unit tests or coverage requirements — they are an additional integration testing strategy layered on top. They validate the entire pipeline (not just individual functions) at increasing complexity levels before you invest time debugging on the full 5×5 board.

Run a full pipeline test at each grid size, in order, before advancing:

| Stage | Grid | What to validate |
|-------|------|-----------------|
| 1 | 2×2 | Agents initialize, MCP servers respond, 1 sub-game completes, no crash |
| 2 | 3×3 | NL messages exchange correctly, fog of war masks positions, belief state updates |
| 3 | 4×4 | Visibility radius creates genuine uncertainty, barriers block correctly, scorer accumulates |
| 4 | 5×5 | Full 6-game series completes autonomously, JSON report generated, email sent |

Each stage has a dedicated integration test file:
- `test_sanity_2x2.py`
- `test_sanity_3x3.py`
- `test_sanity_4x4.py`
- `test_sanity_5x5.py`

Grid size is injected via config override — no code changes needed between stages.

### 11.4 Test files
- `test_board.py`, `test_barriers.py`, `test_movement.py`, `test_fog_of_war.py`
- `test_turn_manager.py`, `test_scorer.py`, `test_sub_game.py`, `test_full_game.py`
- `test_cop_server.py`, `test_thief_server.py` (token auth tested explicitly)
- `test_client.py`, `test_llm_loop.py`, `test_belief_state.py`
- `test_nlp_parser.py`, `test_prompt_builder.py`
- `test_gatekeeper.py`
- `test_json_builder.py`, `test_gmail_sender.py`
- `test_file_size.py`
- `test_sanity_2x2.py`, `test_sanity_3x3.py`, `test_sanity_4x4.py`, `test_sanity_5x5.py`

### 11.5 Run tests
```bash
uv run pytest tests/ --cov=src --cov-fail-under=85
```

---

## Phase 11.5 — Extensibility & ISO/IEC 25010 Alignment

### Extensibility Design
The system must be designed so future capabilities can be added **without changing core logic**. Required extension points:

| Extension point | Where | How |
|----------------|-------|-----|
| New LLM provider | `src/api_gateway/gatekeeper.py` | Provider abstraction — swap Gemini for another via config, no code change |
| New agent strategy | `src/strategy/` | Strategy interface — new strategy class implementing the same interface plugs in without touching orchestrator |
| New MCP tool | `src/mcp_servers/` | FastMCP decorator pattern — add a new tool without modifying existing ones |
| New consumer (CLI, web) | `src/sdk/game_sdk.py` | All new consumers use the SDK — no new access to internals |
| Larger grid | `config/config.json` | `grid_size` is fully configurable — engine, fog of war, and GUI all read from config |

### ISO/IEC 25010 Quality Dimensions
Document compliance with each dimension in `docs/PLAN.md` and `README.md`:

| Dimension | How this project addresses it |
|-----------|------------------------------|
| Functional suitability | Game rules enforced by engine; all 6 sub-games complete correctly |
| Performance efficiency | API Gatekeeper controls rate; no unnecessary LLM calls; configurable timeouts |
| Reliability | Technical failures trigger automatic reruns; retries in gatekeeper |
| Security | Token auth on MCP servers; OAuth for Gmail; no secrets in repo |
| Maintainability | Modular structure; 150-line limit; SDK separation; TDD; zero lint violations |
| Portability | Config-driven (no hardcoded OS paths or values); `uv` for reproducible environments |

---

## Phase 12 — Linting & Code Quality

- `uv run ruff check src/ tests/` — must return zero violations
- No hardcoded values in `src/` (all from config or environment)
- All files ≤ 150 code lines
- Full docstrings on all modules, classes, and public functions
- Consistent naming throughout

---

## Phase 13 — README.md (Scientific Report)

Required sections:
1. Project overview and motivation
2. Formal Dec-POMDP model — tuple ⟨n, S, {Aᵢ}, P, R, {Ωᵢ}, O, γ⟩ with definitions
3. System architecture — C4 diagrams, deployment diagram, ISO/IEC 25010 alignment table
4. MCP communication design — tools, NL message format, NLP parsing, fog of war
5. Strategy description — heuristic with justification
6. Installation & usage — `uv sync`, `uv run`, config guide, contribution guidelines, license
7. GUI screenshots — every meaningful game state (start, mid-game, capture, series complete)
8. Nielsen's heuristics evaluation — table applied to this GUI
9. MCP communication logs — local and Render cloud evidence
10. Results & analysis — win rates, score distributions, average moves across 6 sub-games
11. Parameter sensitivity analysis — vary `visibility_radius` (1, 2, 3) and `max_barriers` (3, 5), measure cop win rate and avg moves; quantitative comparison with charts
12. Visualizations — bar charts, line charts, heatmaps, box plots (Matplotlib/Seaborn/Plotly); all with labels, legends, captions, and high resolution
13. Cost analysis — input tokens, output tokens, cost per Gemini call, total for 6-game series, cost forecast at 100 games
14. Prompt Engineering Log — major prompts used during AI-assisted development, purpose, example outputs, iterations, lessons learned (also kept in `docs/PROMPT_LOG.md`)
15. Test results — summary of pass/fail report; logs from one successful and one failed run saved in `results/`
16. Third-party credits and license

---

## Phase 14 — Final Checklist Before Submission

| Area | Check |
|------|-------|
| `README.md` in root | ✓ |
| `docs/PRD.md`, `PLAN.md`, `TODO.md` | ✓ |
| Dedicated PRDs for 5 mechanisms | ✓ |
| All 8 ISO/IEC 25010 dimensions documented in PLAN + README | ✓ |
| No hardcoded secrets or config values | ✓ |
| `.env-example` with placeholders | ✓ |
| `.gitignore` covers `.env`, credentials | ✓ |
| `pyproject.toml` + `uv.lock` committed | ✓ |
| `__init__.py` + `__all__` in every `src/` package | ✓ |
| All imports use relative or package-based paths only | ✓ |
| SDK layer present — GUI uses only `GameSDK` | ✓ |
| Business logic fully separated from infrastructure | ✓ |
| All files ≤ 150 code lines | ✓ |
| Mixins used where classes exceed 150 lines | ✓ |
| Comments explain "why", not just "what" | ✓ |
| Zero Ruff violations | ✓ |
| ≥ 85% test coverage | ✓ |
| `conftest.py` holds all shared fixtures | ✓ |
| Every public function has normal-path + failure-path test | ✓ |
| Progressive sanity checks pass (2×2 → 5×5) | ✓ |
| Fog of war active — opponent position masked | ✓ |
| NL communication enforced — no raw coordinates | ✓ |
| NLP parser translates text to tool calls | ✓ |
| Token auth on both MCP servers | ✓ |
| 6 sub-games run autonomously end-to-end | ✓ |
| Email received with valid JSON only | ✓ |
| Public Render URLs for both MCP servers | ✓ |
| GUI uses SDK only — no direct module imports | ✓ |
| Nielsen's heuristics evaluated and documented | ✓ |
| GUI screenshots (all states) in README | ✓ |
| Extensibility design documented (plugin/interface pattern) | ✓ |
| MCP communication logs documented | ✓ |
| Prompt Engineering Log included | ✓ |
| All commands use `uv run` (no raw `pip`/`python`) | ✓ |
| `src/version.py` with `VERSION = "1.00"` present | ✓ |
| Config validation runs at startup (version check) | ✓ |
| CI/CD pipeline passes on every commit | ✓ |
| Git: feature branches + meaningful commits + tagged milestones | ✓ |
| `docs/PROMPT_LOG.md` maintained throughout development | ✓ |
| Thread safety on MCP server shared state | ✓ |
| Edge cases documented in comments + covered by tests | ✓ |
| Logging via `logging` module (not print) in all modules | ✓ |
| Test pass/fail report + run logs saved in `results/` | ✓ |
| Parameter sensitivity analysis in notebook (visibility_radius, max_barriers) | ✓ |
| Token cost tracked per sub-game + forecast in README | ✓ |
| Gatekeeper queue: configurable depth, backpressure, drain | ✓ |

---

## Recommended Development Order

| Stage | Task | Focus |
|-------|------|-------|
| 1 | Write all docs (Phase 1) | Planning |
| 2 | Scaffold project + config (Phase 2) | Infrastructure |
| 3 | Core game engine + fog of war + tests (Phase 3) | Game logic |
| 4 | MCP servers locally with token auth (Phase 4) | Communication |
| 5 | Orchestrator + Gemini LLM loop + NLP parser (Phase 5) | Orchestration |
| 6 | Strategy implementation (Phase 6) | Decision-making |
| 7 | Sanity checks: 2×2 → 3×3 → 4×4 → 5×5 (Phase 11) | Integration |
| 8 | GUI (Phase 8) | Visualization |
| 9 | Deploy to Render + token auth in cloud (Phase 9) | Deployment |
| 10 | Gmail reporting (Phase 10) | Automation |
| 11 | Full 6-game end-to-end run + fix failures | Integration |
| 12 | Linting, coverage, README | Polish |
