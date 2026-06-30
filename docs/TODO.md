# Project TODO List: MCP-Based Dual AI Agent Cops-and-Robbers

## Assignment Context
Build a fully autonomous Cops-and-Robbers pursuit game on a 5×5 grid where two AI agents (Cop and Thief) communicate through FastMCP servers using free-form natural language (no rigid coordinate protocols or raw coordinates). The system must handle partial observability (Fog of War via `ObservedState`) and run 6 consecutive sub-games without manual intervention.
**Required deliverables:** SDK-based central architecture (`GameSDK` facade) · public cloud deployment (Render free tier) with token-based authentication · automated JSON reporting via Gmail API OAuth2 · Dec-POMDP scientific README · high-quality visualizations, parameter sensitivity analysis, and full test logs.

---

## ⚠️ Convention: USER ACTION REQUIRED
Tasks marked `[USER ACTION REQUIRED]` cannot be completed by the assistant. They require you (the student) to take a manual step — such as opening a browser, inserting a key, uploading a file, or clicking in a web interface.

**Workflow rule:** When the assistant reaches a `[USER ACTION REQUIRED]` task, it will **stop and wait**. You complete your step, confirm it is done (e.g., "done", "key added", "screenshots saved"), and only then will the assistant continue to the next task.

These tasks are marked with 🧑 in the task line for quick scanning.

---

## Global Mandate: Code Modularity & QA Protocol
Every Python (.py) file created or modified in this project is subject to a strict 3-step continuous protocol:
1. **Implementation:** Write and implement the required logic strictly utilizing `uv` for all environment and dependency management. Direct calls to `pip`, `python -m pip`, `pytest`, or `python -m pytest` are forbidden everywhere — in code, CI, and shell.
2. **Size Verification & Refactoring:** Check the file length immediately after writing it. If the file exceeds **150 lines of code**, pause and split it before moving on — extract Mixins, Helpers, or Constants into separate modules. The assistant will run `wc -l` after every file creation and refactor automatically if the limit is exceeded.
3. **Quality Assurance:** After every phase, run `uv run ruff check src/ tests/` (must return 0 violations) and `uv run pytest tests/ --cov=src --cov-fail-under=85` (must pass). The assistant will not advance to the next phase until both checks are green.

*Note: Documentation (.md) and configuration files (.json, .toml, .yaml) are exempt from this 3-step sequence.*

---

## Phase 1: Planning and Documentation
**Priority:** High | **Status:** Completed
**Definition of Done (DoD):** All foundational design documents (PRD, PLAN, TODO, and dedicated mechanism PRDs) are fully written, committed, and align with ISO/IEC 25010 quality dimensions — before any code is written.

### 1.1 Core Requirements & Architecture
- [x] 1.1.1 [Completed] [Architect] - Write `docs/PRD.md` including purpose, KPIs, 44 functional requirements, 47 non-functional requirements across 12 subsections, user stories, and 9 milestones | DoD: Document committed; all FRs and NFRs traceable to assignment requirements.
- [x] 1.1.2 [Completed] [Architect] - Write `docs/PLAN.md` using the C4 model, ADRs (ADR-01 through ADR-09), data schemas (GameState, ObservedState, SubGameResult), API contracts, and deployment diagrams for local and Render cloud | DoD: Document committed with all architectural diagrams and ADR justifications.
- [x] 1.1.3 [Completed] [Architect] - Write `docs/TODO.md` (this file) in hierarchical checklist format with role, status, and Definition of Done per task | DoD: All phases covered; every task follows the `- [ ] ID [Status] [Role] - Task | DoD:` pattern.

### 1.2 Dedicated Mechanism PRDs
- [x] 1.2.1 [Completed] [Architect] - Write `docs/PRD_game_engine.md` defining the Dec-POMDP model, grid rules, fog-of-war ObservedState spec, win conditions, and edge cases | DoD: All engine inputs/outputs, constraints, and test scenarios documented.
- [x] 1.2.2 [Completed] [Architect] - Write `docs/PRD_mcp_servers.md` defining FastMCP setup, three exposed tools, token-based auth, thread safety, and Render deployment | DoD: Auth flow, tool contracts, and deployment steps fully specified.
- [x] 1.2.3 [Completed] [Architect] - Write `docs/PRD_nlp_communication.md` defining NL message rules, forbidden coordinate patterns, NLP parser spec, belief state update rules, and prompt design | DoD: Parser spec and belief update algorithm documented; forbidden-pattern enforcement specified.
- [x] 1.2.4 [Completed] [Architect] - Write `docs/PRD_strategy.md` defining heuristic cop/thief logic (Manhattan distance), barrier placement heuristic, and optional Q-Learning extension | DoD: Both heuristic and RL approaches documented; success criteria defined.
- [x] 1.2.5 [Completed] [Architect] - Write `docs/PRD_reporting.md` defining Gmail API OAuth2 setup, exact JSON report schema, email trigger logic, and security requirements | DoD: Full setup guide, JSON schema, and test scenarios documented.

### 1.3 Ongoing Logs
- [x] 1.3.1 [Completed] [Developer] - Initialize `docs/PROMPT_LOG.md` with the standard entry template; write the first entry for the initial Gemini agent prompt | DoD: File exists with at least one complete entry (purpose, prompt text, example output, iterations, lessons learned).

---

## Phase 2: Scaffolding & Infrastructure
**Priority:** High | **Status:** Not Started
**Definition of Done (DoD):** Repository initialized; `uv sync` succeeds; all packages, config files, environment templates, CI/CD pipeline, and SDK facade in place; zero Ruff violations; all fixtures committed.

### 2.1 Repository & Project Setup
- [x] 2.1.1 [Completed] [DevOps] - Initialize Git repository with `.gitignore` excluding `.env`, `*.key`, `*.pem`, `token.json`, and `my_google.json` by path pattern | DoD: `git status` shows no secrets; first commit pushed to remote.
- [x] 2.1.2 [Completed] [Developer] - Create `pyproject.toml` as single source of truth: project name, version `1.0.0`, all dependencies, Ruff config (line-length 100, select E/F/W/I/N/UP/B/C4/SIM), and pytest config | DoD: `uv sync` completes; `uv run ruff check` returns 0 violations on empty `src/`.
- [x] 2.1.3 [Completed] [Developer] - Create `src/version.py` containing `VERSION = "1.00"` | DoD: Version matches `pyproject.toml` and all `config/*.json` files; verified by a unit test.
- [x] 2.1.4 [Completed] [Developer] - Create `.env-example` listing all required environment variables with placeholder values: `GEMINI_API_KEY`, `GMAIL_CREDENTIALS_PATH`, `COP_MCP_TOKEN`, `THIEF_MCP_TOKEN` | DoD: File committed; `.env` itself absent from the repo.

### 2.2 🧑 USER ACTION — API Keys Setup
> **PAUSE — Assistant stops here and waits for you to complete 2.2.1 and 2.2.2 before continuing.**

- [x] 2.2.1 [Completed] 🧑 - Go to [Google AI Studio](https://aistudio.google.com/app/apikey) and generate a free Gemini API key | DoD: You have a key string that starts with `AIza...`; ready to paste into `.env`.
- [x] 2.2.2 [Completed] 🧑 - Create a local `.env` file (never committed) by copying `.env-example`; fill in `GEMINI_API_KEY` with the key from 2.2.1; set `COP_MCP_TOKEN` and `THIEF_MCP_TOKEN` to any two strong random strings (e.g., use `python -c "import secrets; print(secrets.token_hex(32))"`) | DoD: `.env` exists locally; `uv run python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('GEMINI_API_KEY'))"` prints the key (not `None`).

### 2.3 Package Structure
- [x] 2.3.1 [Completed] [Developer] - Create the full `src/` directory tree with `__init__.py` (including `__all__`) in every subdirectory: `game/`, `mcp_servers/`, `orchestrator/`, `strategy/`, `api_gateway/`, `reporting/`, `gui/`, `sdk/` | DoD: Every package is importable; relative imports used throughout.
- [x] 2.3.2 [Completed] [Developer] - Create `config/config.json` with all game parameters: `version`, `grid_size`, `max_moves`, `num_games`, `max_barriers`, `visibility_radius`, `llm_provider: "gemini"`, `student_id`, and MCP server URLs (localhost for now; updated in Phase 9) | DoD: No hardcoded game parameters remain in any `.py` file.
- [x] 2.3.3 [Completed] [Developer] - Create `config/rate_limits.json` with Gemini rate-limit parameters: `requests_per_minute`, `max_queue_depth`, `retry_delay_seconds`, `max_retries` | DoD: Gatekeeper reads all values from this file at startup; no defaults hardcoded.

### 2.4 Config Validation & SDK
- [x] 2.4.1 [Completed] [Developer] - Implement `src/sdk/config_validator.py` — reads `config.json` and `rate_limits.json` at startup; checks `version` field against `src/version.py`; raises `ConfigVersionError` with a clear message on mismatch | DoD: Unit test confirms `ConfigVersionError` raised on mismatched version; clean config passes silently. File ≤ 150 lines.
- [x] 2.4.2 [Completed] [Developer] - Implement `src/sdk/game_sdk.py` as the `GameSDK` facade exposing all public methods (`start_game`, `get_observed_state`, `submit_action`, `send_report`) | DoD: GUI and tests import only `GameSDK`; `grep -r "from src.game" src/gui/` returns no matches. File ≤ 150 lines; split into `game_sdk.py` + `game_sdk_mixins.py` if needed.

### 2.5 CI/CD & Git Workflow
- [x] 2.5.1 [Completed] [DevOps] - Create `.github/workflows/ci.yml` running on every push/PR: `uv sync` → `uv run ruff check src/ tests/` → `uv run pytest tests/ --cov=src --cov-fail-under=85` | DoD: Pipeline passes on `main`; direct `pytest` calls absent from YAML.

### 2.6 Test Infrastructure
- [x] 2.6.1 [Completed] [QA] - Create `tests/conftest.py` with all 6 shared fixtures: `minimal_config`, `board_5x5`, `observed_state_factory`, `mock_gemini_client`, `mock_mcp_client`, `sub_game_result_factory` | DoD: All fixtures defined; each used by at least one test; `uv run pytest tests/conftest.py` passes.

### ✅ Phase 2 Quality Gate
- [x] 2.QG.1 [Completed] [QA] - Run `uv run ruff check src/ tests/` and confirm 0 violations | DoD: Output is `All checks passed.`
- [x] 2.QG.2 [Completed] [QA] - Run `uv run pytest tests/ --cov=src` and confirm all Phase 2 tests pass | DoD: No failures; coverage reported (< 85% acceptable at this stage since only scaffolding exists).
- [x] 2.QG.3 [Completed] [QA] - Run `find src/ -name "*.py" | xargs wc -l | sort -rn` and confirm every file is ≤ 150 lines | DoD: No file exceeds the limit; any that do are refactored before advancing to Phase 3.

---

## Phase 3: Core Game Engine
**Priority:** High | **Status:** Not Started
**Definition of Done (DoD):** All game engine modules implemented, individually tested (≥ 85% coverage), all files ≤ 150 lines, zero Ruff violations, and a 2×2 sanity-check integration test passes end-to-end.

### 3.1 Board & Movement
- [x] 3.1.1 [Completed] [Developer] - Implement `src/game/board.py`: configurable grid, cell types (empty, barrier, agent), and boundary validation | DoD: Unit tests confirm correct initialization; out-of-bounds cells rejected; no hardcoded 5×5 dimensions. File ≤ 150 lines.
- [x] 3.1.2 [Completed] [Developer] - Implement `src/game/movement.py`: 8-direction movement (N, NE, E, SE, S, SW, W, NW), blocked-cell rejection, and Thief-first turn resolution | DoD: All 8 directions tested; barrier and boundary blocks tested; move order verified. File ≤ 150 lines.

### 3.2 Barriers
- [x] 3.2.1 [Completed] [Developer] - Implement `src/game/barriers.py`: hard cap of 5 barriers per Cop per sub-game; 6th attempt rejected and logged at WARNING without consuming the turn; barriers impassable immediately after placement | DoD: Cap enforcement, overwrite rejection, and impassability all unit tested. File ≤ 150 lines.

### 3.3 State & Fog of War
- [x] 3.3.1 [Completed] [Developer] - Implement `src/game/game_state.py` as a `frozen=True` dataclass holding full ground-truth state (both positions, all barrier locations, move count); never passed directly to agents | DoD: Immutability tested; no module outside `src/game/` receives a raw `GameState`. File ≤ 150 lines.
- [x] 3.3.2 [Completed] [Developer] - Implement `src/game/observed_state.py` as a `frozen=True` dataclass: `own_pos`, `known_barriers`, `opponent_visible`, `opponent_pos_if_visible`, `move_count`, `barriers_remaining` | DoD: `opponent_pos_if_visible` is always `None` when `opponent_visible` is `False`; no additional state leaks. File ≤ 150 lines.
- [x] 3.3.3 [Completed] [Developer] - Implement `src/game/fog_of_war.py`: apply Chebyshev-distance visibility filter (≤ `visibility_radius`) to produce `ObservedState` from `GameState` | DoD: Opponent masked at distance 3 with radius 2; visible at distance 1; barriers always included. File ≤ 150 lines.

### 3.4 Turn & Game Loop
- [x] 3.4.1 [Completed] [Developer] - Implement `src/game/turn_manager.py`: sequence Thief→Cop each turn; detect win conditions; signal technical failures | DoD: Turn order verified; both win conditions tested; technical failure propagated correctly. File ≤ 150 lines.
- [x] 3.4.2 [Completed] [Developer] - Implement `src/game/scorer.py`: compute per-sub-game scores; accumulate totals into `ScoreSummary` dataclass across all 6 sub-games | DoD: Cop-win and thief-win scoring tested; cumulative totals correct after 6 games. File ≤ 150 lines.
- [x] 3.4.3 [Completed] [Developer] - Implement `src/game/sub_game.py`: run one sub-game loop up to `max_moves` turns; on technical failure, invalidate and flag for automatic rerun without counting toward the 6 | DoD: Happy path (cop wins, thief wins) and technical failure rerun path all tested. File ≤ 150 lines.
- [x] 3.4.4 [Completed] [Developer] - Implement `src/game/full_game.py`: orchestrate exactly 6 valid sub-games; rerun invalid ones automatically; trigger `GameSDK.send_report()` after the 6th valid game | DoD: 6-game series completes without manual intervention; report triggered exactly once. File ≤ 150 lines.

### 3.5 Logging & Edge Cases
- [x] 3.5.1 [Completed] [Developer] - Add `logging` module instrumentation to all `src/game/` files: level, timestamp, and context on every significant event; remove all `print()` calls | DoD: `grep -r "print(" src/game/` returns no matches; log output is parseable.
- [x] 3.5.2 [Completed] [QA] - Write and pass `tests/integration/test_sanity_2x2.py`: one complete sub-game on a 2×2 grid; no crash; correct turn order; accurate win detection | DoD: Test passes with `uv run pytest`; result logged to `results/sanity_2x2.log`.

### ✅ Phase 3 Quality Gate
- [x] 3.QG.1 [Completed] [QA] - Run `uv run ruff check src/ tests/` → must return 0 violations | DoD: Output is `All checks passed.`
- [x] 3.QG.2 [Completed] [QA] - Run `uv run pytest tests/ --cov=src --cov-fail-under=85` → must pass | DoD: All tests green; coverage ≥ 85%.
- [x] 3.QG.3 [Completed] [QA] - Run `find src/ -name "*.py" | xargs wc -l | sort -rn` → every file ≤ 150 lines | DoD: No file exceeds limit; any oversized file refactored before Phase 4 begins.

---

## Phase 4: MCP Servers
**Priority:** High | **Status:** Not Started
**Definition of Done (DoD):** Both FastMCP servers start locally; all three tools callable; token auth returns 401 on failure; concurrent requests do not corrupt shared state; all tests pass; all files ≤ 150 lines.

### 4.1 Server Implementation
- [ ] 4.1.1 [Not Started] [Developer] - Implement `src/mcp_servers/cop_server.py` as a FastMCP server on port 8001 exposing `validate_position`, `send_message`, and `receive_message`; no game logic inside the server | DoD: Server starts with `uv run`; all three tools callable via MCP client. File ≤ 150 lines; split into `cop_server.py` + `server_tools.py` if needed.
- [ ] 4.1.2 [Not Started] [Developer] - Implement `src/mcp_servers/thief_server.py` as a FastMCP server on port 8002 with the same three tools | DoD: Server starts independently; identical auth behavior to cop server. File ≤ 150 lines.

### 4.2 Authentication & Thread Safety
- [ ] 4.2.1 [Not Started] [Developer] - Implement FastMCP middleware in both servers validating `Authorization: Bearer <token>` from the environment variable (`COP_MCP_TOKEN` / `THIEF_MCP_TOKEN`); missing or wrong token → 401; token never hardcoded | DoD: Valid token → tool executes; missing token → 401; wrong token → 401; all three scenarios tested. File impact ≤ 150 lines per file.
- [ ] 4.2.2 [Not Started] [Developer] - Protect shared message store in both servers with `threading.Lock()`; document in code comments why the lock is placed where it is | DoD: Concurrent-request test passes without data corruption; lock acquisition/release logged at DEBUG level.

### 4.3 Testing
- [ ] 4.3.1 [Not Started] [QA] - Write `tests/test_cop_server.py` and `tests/test_thief_server.py`: valid token + all 3 tools (happy path), missing token (401), invalid token (401), `send_message` → `receive_message` round-trip, two concurrent `send_message` calls | DoD: All tests pass; coverage ≥ 85% for both server files.

### ✅ Phase 4 Quality Gate
- [ ] 4.QG.1 [Not Started] [QA] - Run `uv run ruff check src/ tests/` → 0 violations | DoD: `All checks passed.`
- [ ] 4.QG.2 [Not Started] [QA] - Run `uv run pytest tests/ --cov=src --cov-fail-under=85` → all pass | DoD: Green; ≥ 85% coverage.
- [ ] 4.QG.3 [Not Started] [QA] - Run `find src/ -name "*.py" | xargs wc -l | sort -rn` → every file ≤ 150 lines | DoD: No oversized files; any that do are refactored before Phase 5.

---

## Phase 5: Orchestrator & LLM Loop
**Priority:** High | **Status:** Not Started
**Definition of Done (DoD):** MCP client connects to both servers with token injection; Gemini generates NL messages and actions; NLP parser extracts intentions; belief state updates correctly; 3×3 sanity-check passes.

### 5.1 MCP Client
- [ ] 5.1.1 [Not Started] [Developer] - Implement `src/orchestrator/client.py` connecting to both MCP servers, injecting the correct auth token per server, and exposing typed wrappers for all three tools | DoD: Client connects locally and to Render HTTPS URLs (via config); 401 triggers error handling. File ≤ 150 lines.

### 5.2 LLM Integration
- [ ] 5.2.1 [Not Started] [Developer] - Implement `src/orchestrator/llm_loop.py` sending structured prompts to Gemini via the API Gatekeeper and feeding responses to the NLP parser; empty or malformed response treated as technical failure | DoD: LLM call routed through Gatekeeper; tokens logged per call; failure path tested with a mock. File ≤ 150 lines.
- [ ] 5.2.2 [Not Started] [Developer] - Implement `src/orchestrator/prompt_builder.py` constructing each agent's turn prompt from: role description, `ObservedState`, received NL message, belief state summary, list of valid actions, and the explicit instruction "never include numeric coordinates" | DoD: Forbidden-coordinate instruction always present in output; prompt templates logged in `docs/PROMPT_LOG.md`. File ≤ 150 lines.

### 5.3 NLP & Belief State
- [ ] 5.3.1 [Not Started] [Developer] - Implement `src/orchestrator/nlp_parser.py` extracting an `IntentionResult` (action, direction, target_cell, confidence, raw_text) from raw LLM text using keyword matching with heuristic fallback (confidence < 0.5 → strategy module decides) | DoD: Parser tested with ≥ 10 diverse NL inputs; all results logged at DEBUG. File ≤ 150 lines.
- [ ] 5.3.2 [Not Started] [Developer] - Implement `src/orchestrator/belief_state.py` maintaining a probability distribution over all board cells; update rules: direct observation → certainty; NL inference → regional boost; movement prior → diffusion kernel; barriers → zero probability | DoD: `most_likely_pos()` and `probability_map()` tested; direct-observation test sets probability to 1.0 at visible cell. File ≤ 150 lines; split into `belief_state.py` + `belief_updater.py` if needed.

### 5.4 Testing
- [ ] 5.4.1 [Not Started] [QA] - Write `tests/test_nlp_parser.py` asserting that no agent message matches forbidden coordinate regex `\(\d+,\s*\d+\)` or `\[\d+,\s*\d+\]` across ≥ 20 sample LLM outputs | DoD: Zero coordinate leaks detected; test passes.
- [ ] 5.4.2 [Not Started] [QA] - Write and pass `tests/integration/test_sanity_3x3.py`: one complete sub-game on 3×3 with NL messages exchanged and belief state updated each turn | DoD: NL messages non-empty; belief state changes observed between turns; result logged to `results/sanity_3x3.log`.

### ✅ Phase 5 Quality Gate
- [ ] 5.QG.1 [Not Started] [QA] - `uv run ruff check src/ tests/` → 0 violations | DoD: `All checks passed.`
- [ ] 5.QG.2 [Not Started] [QA] - `uv run pytest tests/ --cov=src --cov-fail-under=85` → all pass | DoD: Green; ≥ 85%.
- [ ] 5.QG.3 [Not Started] [QA] - `find src/ -name "*.py" | xargs wc -l | sort -rn` → every file ≤ 150 lines | DoD: No oversized files; refactor before Phase 6.

---

## Phase 6: Agent Strategy
**Priority:** High | **Status:** Not Started
**Definition of Done (DoD):** Both heuristic strategies select valid actions in < 5 ms; barrier placement logic correct; 4×4 sanity-check passes with fog of war creating genuine uncertainty.

### 6.1 Heuristic Strategies
- [ ] 6.1.1 [Not Started] [Developer] - Implement `src/strategy/heuristic_cop.py`: select the valid neighbor minimizing Manhattan distance to `belief_state.most_likely_pos()`; place barrier when `barriers_remaining > 0` and it would block a high-probability thief escape corridor | DoD: Cop never selects `place_barrier` when `barriers_remaining == 0`; pursuit direction unit tested. File ≤ 150 lines.
- [ ] 6.1.2 [Not Started] [Developer] - Implement `src/strategy/heuristic_thief.py`: select the valid neighbor maximizing Manhattan distance from estimated cop position; tie-break by avoiding corner cells | DoD: Thief moves away from corners when adjacent and cop is approaching; evasion direction unit tested. File ≤ 150 lines.

### 6.2 Integration
- [ ] 6.2.1 [Not Started] [QA] - Write and pass `tests/integration/test_sanity_4x4.py`: one complete sub-game on 4×4 where fog of war causes `opponent_visible = False` on majority of turns | DoD: Test passes; log confirms > 50% of turns are fog-of-war turns; result logged to `results/sanity_4x4.log`.

### ✅ Phase 6 Quality Gate
- [ ] 6.QG.1 [Not Started] [QA] - `uv run ruff check src/ tests/` → 0 violations | DoD: `All checks passed.`
- [ ] 6.QG.2 [Not Started] [QA] - `uv run pytest tests/ --cov=src --cov-fail-under=85` → all pass | DoD: Green; ≥ 85%.
- [ ] 6.QG.3 [Not Started] [QA] - `find src/ -name "*.py" | xargs wc -l | sort -rn` → every file ≤ 150 lines | DoD: No oversized files; refactor before Phase 7.

---

## Phase 7: API Gatekeeper
**Priority:** High | **Status:** Not Started
**Definition of Done (DoD):** All Gemini and Gmail calls route exclusively through the Gatekeeper; rate limits enforced; queue thread-safe; token usage logged per call; all tests pass.

### 7.1 Core Gatekeeper
- [ ] 7.1.1 [Not Started] [Developer] - Implement `src/api_gateway/gatekeeper.py`: single entry point for all Gemini and Gmail calls; enforce rate limits from `rate_limits.json`; FIFO queue with configurable max depth | DoD: `grep -rn "genai\." src/ | grep -v gatekeeper` returns no matches (no direct Gemini calls outside gatekeeper). File ≤ 150 lines; split into `gatekeeper.py` + `queue_manager.py` if needed.
- [ ] 7.1.2 [Not Started] [Developer] - Implement backpressure (block callers when queue is full) and queue drain (resume when rate window resets); protect queue and counters with thread-safe structures | DoD: Concurrent stress test confirms no queue corruption under 2 simultaneous callers.
- [ ] 7.1.3 [Not Started] [Developer] - Implement retry logic with configurable delay/max retries from `rate_limits.json`; log every API call: provider, input tokens, output tokens, estimated cost (USD), latency (ms), success/fail | DoD: Token log file written after each call; retry attempts logged at WARNING level.

### 7.2 Testing
- [ ] 7.2.1 [Not Started] [QA] - Write `tests/test_gatekeeper.py` covering: rate limit enforcement (burst blocked), FIFO queue order, backpressure when full, retry on failure (mock 2 failures then success), and thread safety (2 concurrent callers) | DoD: All 5 scenarios pass; no flakiness across 3 consecutive runs.

### ✅ Phase 7 Quality Gate
- [ ] 7.QG.1 [Not Started] [QA] - `uv run ruff check src/ tests/` → 0 violations | DoD: `All checks passed.`
- [ ] 7.QG.2 [Not Started] [QA] - `uv run pytest tests/ --cov=src --cov-fail-under=85` → all pass | DoD: Green; ≥ 85%.
- [ ] 7.QG.3 [Not Started] [QA] - `find src/ -name "*.py" | xargs wc -l | sort -rn` → every file ≤ 150 lines | DoD: No oversized files; refactor before Phase 8.

---

## Phase 8: GUI
**Priority:** High | **Status:** Not Started
**Definition of Done (DoD):** pygame GUI renders correctly for every game state; calls only `GameSDK`; Nielsen's 10 heuristics evaluated; user takes and commits screenshots.

### 8.1 Implementation
- [ ] 8.1.1 [Not Started] [Developer] - Implement `src/gui/board_view.py` rendering: 5×5 grid, Cop and Thief icons, barrier cells, move counter, scores panel, current-status label (whose turn / who won), fog-of-war highlighting | DoD: All game states render without crash; all visual elements labeled (text, not color-only). File ≤ 150 lines; split into `board_view.py` + `ui_components.py` if needed.
- [ ] 8.1.2 [Not Started] [Developer] - Verify GUI calls only `GameSDK` — run `grep -r "from src.game" src/gui/` and confirm no matches | DoD: Grep returns empty; GUI file imports only from `src.sdk`.

### 8.2 UX Evaluation
- [ ] 8.2.1 [Not Started] [Developer] - Evaluate the GUI against Nielsen's 10 usability heuristics and document findings as a table in `README.md` with one row per heuristic (pass/partial/fail + notes) | DoD: Table committed to README; at least 2 identified issues have documented mitigations.

### 8.3 🧑 USER ACTION — Screenshots
> **PAUSE — Assistant stops here and waits for you to complete 8.3.1 before continuing.**

- [ ] 8.3.1 [USER ACTION REQUIRED] 🧑 - Run the game locally (`uv run python -m src.gui.board_view`) and take screenshots of every distinct GUI state: (1) game start / initial board, (2) mid-game with fog of war active, (3) a barrier being placed, (4) cop wins sub-game, (5) thief wins sub-game, (6) full series complete screen | DoD: At least 5 screenshots saved to `assets/screenshots/` with descriptive filenames (e.g., `mid_game_fog.png`); folder committed to repo.

### ✅ Phase 8 Quality Gate
- [ ] 8.QG.1 [Not Started] [QA] - `uv run ruff check src/ tests/` → 0 violations | DoD: `All checks passed.`
- [ ] 8.QG.2 [Not Started] [QA] - `uv run pytest tests/ --cov=src --cov-fail-under=85` → all pass | DoD: Green; ≥ 85%.
- [ ] 8.QG.3 [Not Started] [QA] - `find src/ -name "*.py" | xargs wc -l | sort -rn` → every file ≤ 150 lines | DoD: No oversized files; refactor before Phase 9.

---

## Phase 9: Cloud Deployment
**Priority:** High | **Status:** Not Started
**Definition of Done (DoD):** Both MCP servers live on public Render HTTPS URLs; token auth working; `config.json` updated; full pipeline runs end-to-end with cloud servers.

### 9.1 🧑 USER ACTION — Render Deployment
> **PAUSE — Assistant stops here and waits for you to complete 9.1.1 through 9.1.4 before continuing.**

- [ ] 9.1.1 [USER ACTION REQUIRED] 🧑 - Create a free account at [render.com](https://render.com) (no credit card required) | DoD: Account active; dashboard accessible.
- [ ] 9.1.2 [USER ACTION REQUIRED] 🧑 - In the Render dashboard: create a new Web Service for `cop_server.py`; connect your GitHub repo; set the start command to `uv run python -m src.mcp_servers.cop_server`; set the environment variable `COP_MCP_TOKEN` to the value from your local `.env` | DoD: Render shows "Live" status for the cop server; a public HTTPS URL is displayed (copy it).
- [ ] 9.1.3 [USER ACTION REQUIRED] 🧑 - Create a second Render Web Service for `thief_server.py`; same process as 9.1.2; set `THIEF_MCP_TOKEN` in the Render dashboard | DoD: Render shows "Live" status for the thief server; a second public HTTPS URL is displayed (copy it).
- [ ] 9.1.4 [USER ACTION REQUIRED] 🧑 - Update `config/config.json`: replace `localhost:8001` and `localhost:8002` with the two Render HTTPS URLs from 9.1.2 and 9.1.3 | DoD: `config.json` committed with real Render URLs; no localhost URLs remain in the cloud config.

### 9.2 Cloud Verification
- [ ] 9.2.1 [Not Started] [QA] - Run the full 6-game pipeline end-to-end against both Render HTTPS servers; capture the MCP communication log | DoD: Series completes without manual intervention; log saved to `results/cloud_run.log`; email sent to instructor address.

### ✅ Phase 9 Quality Gate
- [ ] 9.QG.1 [Not Started] [QA] - `uv run ruff check src/ tests/` → 0 violations | DoD: `All checks passed.`
- [ ] 9.QG.2 [Not Started] [QA] - `uv run pytest tests/ --cov=src --cov-fail-under=85` → all pass | DoD: Green; ≥ 85%.
- [ ] 9.QG.3 [Not Started] [QA] - `find src/ -name "*.py" | xargs wc -l | sort -rn` → every file ≤ 150 lines | DoD: No oversized files.

---

## Phase 10: Automated Reporting
**Priority:** High | **Status:** Not Started
**Definition of Done (DoD):** Gmail OAuth2 configured; `token.json` generated and reused silently; JSON report matches exact schema; email arrives at instructor address; all reporting tests pass.

### 10.1 🧑 USER ACTION — Gmail API Setup
> **PAUSE — Assistant stops here and waits for you to complete 10.1.1 through 10.1.4 before continuing.**

- [ ] 10.1.1 [USER ACTION REQUIRED] 🧑 - Go to [Google Cloud Console](https://console.cloud.google.com): create a new project (e.g., "Cops and Robbers"); navigate to **APIs & Services → Library**; search for "Gmail API" and click **Enable** | DoD: Gmail API shows "Enabled" in your project dashboard.
- [ ] 10.1.2 [USER ACTION REQUIRED] 🧑 - In the same project: go to **APIs & Services → OAuth consent screen**; choose **External**; fill in App name and your Gmail as the support email; under **Test users** add your own Gmail address; save | DoD: Consent screen status shows "In production" or "Testing"; your Gmail is listed as a test user.
- [ ] 10.1.3 [USER ACTION REQUIRED] 🧑 - Go to **APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID**; choose **Desktop App**; download the JSON file; **rename it to `my_google.json`**; store it at a path **outside** the project directory (e.g., `~/private_google/my_google.json`) | DoD: `my_google.json` exists outside the project folder; path noted for `.env`; file is NOT in any git-tracked directory.
- [ ] 10.1.4 [USER ACTION REQUIRED] 🧑 - Add `GMAIL_CREDENTIALS_PATH=~/private_google/my_google.json` to your local `.env` file | DoD: `uv run python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('GMAIL_CREDENTIALS_PATH'))"` prints the correct path.

### 10.2 Report Generation & Sending
- [ ] 10.2.1 [Not Started] [Developer] - Implement `src/reporting/json_builder.py` constructing the full JSON report from 6 `SubGameResult` objects plus `llm_usage` totals from the Gatekeeper log, matching the exact schema in `docs/PRD_reporting.md` | DoD: `json.loads(json_builder.build())` succeeds; all required keys present; schema validated by test. File ≤ 150 lines.
- [ ] 10.2.2 [Not Started] [Developer] - Implement `src/reporting/gmail_sender.py` sending the JSON string as the email body (no attachments, no prose) to `rmisegal+uoh26b@gmail.com` with subject `Cops and Robbers — Student ID: <YOUR_STUDENT_ID>`; scope limited to `gmail.send` only | DoD: Email arrives at instructor address with valid JSON body. File ≤ 150 lines.

### 10.3 🧑 USER ACTION — First OAuth Browser Flow
> **PAUSE — Assistant stops here and waits for you to complete 10.3.1 before continuing.**

- [ ] 10.3.1 [USER ACTION REQUIRED] 🧑 - Run `uv run python -m src.reporting.gmail_sender --test-auth` (or equivalent); a browser window will open asking you to grant Gmail Send permission to your app; click **Allow** | DoD: `token.json` is created next to `my_google.json`; a second run completes without opening a browser; `token.json` is NOT committed to the repo.

### 10.4 Testing
- [ ] 10.4.1 [Not Started] [QA] - Write `tests/test_json_builder.py`: schema validation, all required fields, correct accumulation across 6 sub-games, and clear `ValueError` on missing input | DoD: All cases pass; coverage ≥ 85% for `json_builder.py`.
- [ ] 10.4.2 [Not Started] [QA] - Write `tests/test_gmail_sender.py` with mocked Gmail API: correct recipient, subject, JSON-only body, 3-retry on network failure, `FileNotFoundError` on missing credentials | DoD: All mock scenarios pass; no real email sent during test runs.

### ✅ Phase 10 Quality Gate
- [ ] 10.QG.1 [Not Started] [QA] - `uv run ruff check src/ tests/` → 0 violations | DoD: `All checks passed.`
- [ ] 10.QG.2 [Not Started] [QA] - `uv run pytest tests/ --cov=src --cov-fail-under=85` → all pass | DoD: Green; ≥ 85%.
- [ ] 10.QG.3 [Not Started] [QA] - `find src/ -name "*.py" | xargs wc -l | sort -rn` → every file ≤ 150 lines | DoD: No oversized files.

---

## Phase 11: Testing
**Priority:** High | **Status:** Not Started
**Definition of Done (DoD):** All unit tests pass; ≥ 85% coverage enforced by CI; all 4 sanity checks pass; file-size guard active; test logs committed to `results/`.

### 11.1 Unit Tests & Guards
- [ ] 11.1.1 [Not Started] [QA] - Write unit tests for every `src/` module: at minimum one happy-path and one failure-path test per public function; use `conftest.py` fixtures throughout | DoD: `uv run pytest tests/` exits 0; no untested public functions remain.
- [ ] 11.1.2 [Not Started] [QA] - Write `tests/test_file_size.py` that automatically fails if any `.py` file in `src/` exceeds 150 lines of code | DoD: Test fails on a deliberately oversized test file and passes after refactoring; committed to CI pipeline.

### 11.2 Coverage & Progressive Sanity Checks
- [ ] 11.2.1 [Not Started] [QA] - Achieve ≥ 85% test coverage with `uv run pytest --cov=src --cov-fail-under=85` | DoD: CI pipeline enforces this on every push to `main`.
- [ ] 11.2.2 [Not Started] [QA] - Confirm all 4 progressive sanity checks pass consecutively: 2×2 (Phase 3), 3×3 (Phase 5), 4×4 (Phase 6), 5×5 full pipeline | DoD: All 4 integration test files pass in one `uv run pytest tests/integration/` run.
- [ ] 11.2.3 [Not Started] [QA] - Save test run logs to `results/test_pass.log` (one full successful run) and `results/test_fail_example.log` (one failure showing graceful handling) | DoD: Both files committed; referenced in README.

### ✅ Phase 11 Quality Gate
- [ ] 11.QG.1 [Not Started] [QA] - `uv run ruff check src/ tests/` → 0 violations | DoD: `All checks passed.`
- [ ] 11.QG.2 [Not Started] [QA] - `uv run pytest tests/ --cov=src --cov-fail-under=85` → all pass | DoD: Green; ≥ 85%.
- [ ] 11.QG.3 [Not Started] [QA] - `find src/ -name "*.py" | xargs wc -l | sort -rn` → every file ≤ 150 lines | DoD: No oversized files.

---

## Phase 12: Linting & Code Quality
**Priority:** High | **Status:** Not Started
**Definition of Done (DoD):** Zero Ruff violations; all files ≤ 150 lines; all public symbols have docstrings; all non-obvious design choices have "why" comments.

### 12.1 Linting
- [ ] 12.1.1 [Not Started] [Developer] - Achieve zero Ruff violations across all `src/` and `tests/` files with `uv run ruff check src/ tests/` | DoD: CI passes the Ruff check on every commit; no `# noqa` suppressions without documented justification.

### 12.2 File Size & Documentation Quality
- [ ] 12.2.1 [Not Started] [Developer] - Ensure every `src/` file is ≤ 150 lines; refactor any oversized file using Mixins or Helper modules | DoD: `tests/test_file_size.py` passes; no file was compressed by removing necessary logic.
- [ ] 12.2.2 [Not Started] [Developer] - Write complete docstrings for every module, class, and public function (consistent style — NumPy or Google, pick one and apply throughout) | DoD: Manual review confirms no missing docstrings on any public symbol.
- [ ] 12.2.3 [Not Started] [Developer] - Add "why" comments to every non-obvious design choice (e.g., why Chebyshev distance, why FIFO queue, why `threading.Lock` at this exact location) | DoD: Code review confirms every unusual decision has a prose explanation in a comment above it.

### ✅ Phase 12 Quality Gate
- [ ] 12.QG.1 [Not Started] [QA] - `uv run ruff check src/ tests/` → 0 violations | DoD: `All checks passed.` — final time this check fails, the submission is blocked.
- [ ] 12.QG.2 [Not Started] [QA] - `uv run pytest tests/ --cov=src --cov-fail-under=85` → all pass | DoD: Green; ≥ 85% — final confirmation before README phase.
- [ ] 12.QG.3 [Not Started] [QA] - `find src/ -name "*.py" | xargs wc -l | sort -rn` → every file ≤ 150 lines | DoD: Definitive check; no exceptions.

---

## Phase 13: README & Research
**Priority:** High | **Status:** Not Started
**Definition of Done (DoD):** README is a complete scientific report and user manual; parameter analysis notebook committed; cost forecast documented; Prompt Log finalized; final release tagged.

### 13.1 README Sections
- [ ] 13.1.1 [Not Started] [Developer] - Write README sections 1–8: project overview, formal Dec-POMDP model (⟨n, S, {Aᵢ}, P, R, {Ωᵢ}, O, γ⟩ with definitions), system architecture (C4 + ISO 25010 table), MCP communication design, strategy description, installation & usage, GUI screenshots, and Nielsen's 10 heuristics evaluation table | DoD: All 8 sections complete; Dec-POMDP tuple fully defined with notation.
- [ ] 13.1.2 [Not Started] [Developer] - Write README sections 9–16: MCP communication logs (local + Render evidence), results & analysis, parameter sensitivity analysis summary, high-quality visualizations (≥ 3 chart types), cost analysis (per sub-game + 100-game forecast), Prompt Engineering Log summary, test results summary, and credits | DoD: All 8 sections complete; charts present with labels, legends, and captions.

### 13.2 Research & Analysis
- [ ] 13.2.1 [Not Started] [Researcher] - Create `notebooks/results_analysis.ipynb` running parameter sensitivity analysis: vary `visibility_radius` (1, 2, 3) and `max_barriers` (3, 5); measure cop win rate and average moves per sub-game; produce bar charts, line charts, and box plots | DoD: Notebook runs end-to-end; charts saved to `assets/`; quantitative comparison table in README.
- [ ] 13.2.2 [Not Started] [Researcher] - Record precise token accounting from the Gatekeeper log: input tokens, output tokens, Gemini cost per call, total for 6-game series; write 100-game forecast in README cost section | DoD: Numbers in README match the Gatekeeper log file; forecast calculation shown.

### 13.3 Prompt Log & Final Checks
- [ ] 13.3.1 [Not Started] [Developer] - Finalize `docs/PROMPT_LOG.md` with all major AI-assisted development prompts — at least 5 complete entries each with purpose, prompt text, example output, iterations, and lessons learned | DoD: Every significant LLM prompt used during development is logged.

### 13.4 🧑 USER ACTION — Final Release Tag
> **PAUSE — Assistant stops here and waits for you to complete 13.4.1 before the submission is considered done.**

- [ ] 13.4.1 [USER ACTION REQUIRED] 🧑 - Review the final state of the repository; if satisfied, run: `git tag M9-final-submission && git push origin M9-final-submission` | DoD: Tag `M9-final-submission` is visible on GitHub; it points to the commit that passes all CI checks; submission link sent to instructor.
