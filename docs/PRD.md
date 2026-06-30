# Product Requirements Document (PRD)
## Project: Cops & Robbers — Dual AI Agent Pursuit via MCP Servers
**Version:** 1.01  
**Course:** AI Agent Communication Through MCP Servers  
**Institution:** University of Haifa, Department of Computer Science  
**Lecturer:** Dr. Yoram Segal  
**Last Updated:** 2026-06-30  

---

## 1. Project Purpose

This project implements a fully autonomous, multi-agent pursuit game in which two AI agents — a **Cop** and a **Thief** — play against each other on a two-dimensional grid. Each agent operates through its own MCP (Model Context Protocol) server and communicates with its opponent exclusively via **free-form natural language** under **partial observability** (fog of war). The game engine orchestrates a complete series of 6 sub-games continuously without manual intervention and automatically emails a structured JSON report upon completion.

The project demonstrates advanced competency in:
- AI agent orchestration and pipeline design
- Distributed system architecture (MCP servers, cloud deployment on Render)
- Natural language understanding and NLP parsing under partial observability
- SDK-based software architecture with clean separation of concerns
- Secure API integration (OAuth, token-based auth)
- Professional software engineering (TDD, 85% coverage, zero lint violations, 150-line limit)

---

## 2. Problem Statement

Designing multi-agent systems that communicate through structured protocols (e.g., fixed JSON messages with numeric coordinates) is straightforward but does not reflect real-world challenges. The core challenge here is to build agents that:
- Operate with **partial observability** — each agent receives a masked `ObservedState`, never the full board
- Communicate only through **ambiguous free-form natural language** (no raw coordinates)
- Parse natural language to extract intentions and translate them into physical tool executions
- Make real-time decisions under **environmental uncertainty** and potential **deception**

---

## 3. Target Audience

- **Primary:** The course lecturer and graders evaluating the submission
- **Secondary:** The student team building and operating the system

---

## 4. Goals and Success Criteria

### Primary Goals
1. Build two autonomous AI agents (Cop and Thief) that play a complete 6-sub-game series continuously, without manual intervention
2. Implement partial observability (fog of war) — agents receive masked state, not full board truth
3. Enforce strict free-form NL communication with an NLP parser translating text to tool calls
4. Implement MCP-based communication using FastMCP with mandatory token authentication
5. Deploy MCP servers to Render (free tier) with public HTTPS URLs
6. Automatically send a correctly formatted JSON report by email upon game completion
7. Expose all business logic through a central SDK layer; GUI uses only the SDK

### Success Criteria
- 6 valid sub-games complete from start to finish with zero manual intervention
- Agents never transmit raw coordinates — all messages are free-form natural language
- Fog of war active: opponent position masked beyond `visibility_radius` cells
- NLP parser successfully maps agent text to valid tool calls every turn
- Email arrives at `rmisegal+uoh26b@gmail.com` containing only valid JSON
- Both Render MCP server URLs are publicly reachable via HTTPS with token auth
- All code passes Ruff with zero violations
- Test coverage ≥ 85%; progressive sanity checks pass at 2×2, 3×3, 4×4, 5×5
- GUI communicates only through `GameSDK` — no direct module imports

---

## 5. KPIs (Key Performance Indicators)

| KPI | Target |
|-----|--------|
| Sub-game completion rate (no technical failures) | ≥ 90% |
| Average number of moves per sub-game | Tracked and reported |
| Cop win rate (across 6 sub-games) | Tracked and reported |
| Thief survival rate | Tracked and reported |
| Email delivery success | 100% (retry on failure) |
| Test coverage | ≥ 85% |
| Lint violations | 0 |
| Files exceeding 150 code lines | 0 |
| API calls routed through gatekeeper | 100% |
| GUI calls bypassing SDK | 0 |

---

## 6. User Stories

| ID | As a... | I want to... | So that... |
|----|---------|--------------|------------|
| US-01 | Lecturer | Run the game pipeline and receive an email with the JSON report | I can grade the submission automatically |
| US-02 | Student | Configure all game parameters via `config.json` | No code changes are needed to adjust the game |
| US-03 | Student | Run both MCP servers locally first | I can verify the pipeline before deploying to the cloud |
| US-04 | Student | Deploy MCP servers to Render for free | The system works as a distributed architecture without cost |
| US-05 | Cop agent | Send a natural-language message to the Thief each turn | The opponent must infer my position without receiving exact coordinates |
| US-06 | Thief agent | Receive a natural-language message, parse it, and update my belief state | I can make an informed movement decision under partial observability |
| US-07 | Game engine | Run all 6 sub-games automatically in sequence | No manual trigger is needed between games |
| US-08 | Student | View the game in a GUI in real time | I can observe agent behavior and capture screenshots for the README |
| US-09 | Cop agent | Automatically trigger an email report after game 6 | The report is sent without manual action |
| US-10 | Developer | Access all business logic through `GameSDK` | Consumers (GUI, CLI, tests) never import internal modules directly |
| US-11 | Agent | Receive only my `ObservedState` (fog of war) | I cannot cheat by reading the opponent's true position from the full game state |

---

## 7. Functional Requirements

### 7.1 Game Engine
- **FR-01:** The board must be a configurable N×M grid (default 5×5), loaded from `config.json`
- **FR-02:** The Thief moves first, followed by the Cop, alternating each turn
- **FR-03:** Movement is allowed in 8 directions (including diagonals)
- **FR-04:** The Cop may place a barrier on its **current cell** instead of moving; hard limit: exactly **5 barriers per sub-game**; barriers cannot be overwritten; a second attempt beyond 5 must be rejected as an invalid move
- **FR-05:** Barriers make a cell permanently impassable for **both** agents for the remainder of that sub-game; they reset between sub-games
- **FR-06:** The Cop wins a sub-game by occupying the same cell as the Thief
- **FR-07:** The Thief wins a sub-game by surviving all 25 moves without capture
- **FR-08:** A sub-game that terminates due to a technical failure is invalid and must be automatically rerun
- **FR-09:** A full game consists of exactly 6 **valid** sub-games, run continuously without manual intervention
- **FR-10:** Scores are accumulated across all 6 sub-games: Cop win → Cop +20, Thief +5; Thief win → Cop +5, Thief +10

### 7.2 Partial Observability — Fog of War
- **FR-11:** Each agent must receive an `ObservedState` object, never the full `GameState`
- **FR-12:** `ObservedState` exposes: own position, known barriers, move count, barriers remaining (Cop only), and opponent position **only if within `visibility_radius` cells** (configurable, default 2)
- **FR-13:** Outside `visibility_radius`, `opponent_visible = False` and `opponent_pos_if_visible = None` — the agent must infer the opponent's location from NL messages and belief state
- **FR-14:** The fog of war filter (`fog_of_war.py`) must be applied by the engine before any state is passed to the Orchestrator or agents

### 7.3 MCP Servers
- **FR-15:** Two separate FastMCP servers must be implemented — one for the Cop, one for the Thief
- **FR-16:** Each server must expose exactly three tools: `validate_position`, `send_message`, `receive_message`
- **FR-17:** The LLM must NOT reside inside the MCP server; servers expose tools only
- **FR-18:** Every request to both servers must include a valid `Authorization: Bearer <token>` header; missing or invalid tokens receive `401 Unauthorized`
- **FR-19:** Tokens are loaded from environment variables on the server side — never hardcoded; token revocation is supported by updating the environment variable

### 7.4 Orchestrator / MCP Client
- **FR-20:** The MCP client manages the game loop, injects auth tokens, invokes tools, and passes results back to the LLM (Gemini)
- **FR-21:** Each agent must maintain a `belief_state` — a probability distribution over opponent cells, updated each turn
- **FR-22:** Agents must generate free-form natural-language messages — raw coordinate strings (e.g., `"move to (3,2)"`) are strictly forbidden
- **FR-23:** An NLP parser (`nlp_parser.py`) must extract the agent's intended action from its NL text and translate it into a concrete tool invocation
- **FR-24:** The orchestrator must handle technical failures gracefully and trigger automatic sub-game reruns

### 7.5 SDK Layer
- **FR-25:** All business logic must be accessible through a central `GameSDK` class in `src/sdk/`
- **FR-26:** The GUI must communicate **only** through `GameSDK` — direct imports from `src/game/`, `src/orchestrator/`, `src/reporting/`, etc. are forbidden from consumer code
- **FR-27:** Business logic must be completely separated from infrastructure (files, external APIs)

### 7.6 Package Structure
- **FR-28:** Every subdirectory in `src/` must contain an `__init__.py` defining the package's public interface via `__all__`
- **FR-29:** All imports across the codebase must use relative or package-based paths only — absolute filesystem paths (e.g., `sys.path.append(...)`) are strictly forbidden

### 7.7 Configuration
- **FR-30:** All game parameters must be loaded from `config.json` (including `visibility_radius`) — no hardcoded values in source code
- **FR-31:** All API rate limits must be loaded from `config/rate_limits.json`
- **FR-32:** All secrets (API keys, tokens) must be loaded from environment variables only

### 7.8 Automated Email Reporting
- **FR-33:** Upon completion of all 6 sub-games, the report is triggered automatically (via `GameSDK.send_report()`)
- **FR-34:** The email is sent to `rmisegal+uoh26b@gmail.com` using the Gmail API (not SMTP)
- **FR-35:** The email body must contain **only** the JSON report — no additional text
- **FR-36:** Authentication uses Google OAuth2 with `token.json` stored **outside** the project directory
- **FR-37:** The Gmail credential JSON file (`my_google.json`) must reside in a private folder outside the repository

### 7.9 GUI
- **FR-38:** A pygame graphical interface must display the grid, agent positions, barriers, sub-game number, move counter, turn indicator, barriers remaining, and cumulative scores in real time
- **FR-39:** GUI must call only `GameSDK` methods — no direct game module imports
- **FR-40:** GUI screenshots (all meaningful states) must be included in the README

### 7.10 Cloud Deployment
- **FR-41:** Both MCP servers must be deployed to **Render** (free tier — no credit card required)
- **FR-42:** Each server must have a publicly reachable HTTPS URL (auto-provided by Render)
- **FR-43:** `COP_MCP_TOKEN` and `THIEF_MCP_TOKEN` must be set as environment variables in Render's dashboard — not in committed files
- **FR-44:** Servers must not be deployed from a workplace or institutional network with restrictive firewall policies

---

## 8. Non-Functional Requirements

### 8.1 Code Quality
- **NFR-01:** Zero Ruff lint violations (rules: `select = ["E","F","W","I","N","UP","B","C4","SIM"]`, `line-length = 100`)
- **NFR-02:** No single source file in `src/` may exceed 150 lines of code (blank lines and comment lines excluded)
- **NFR-03:** All modules, classes, and public functions must have full docstrings
- **NFR-04:** Code must follow single-responsibility and OOP principles; no duplicated logic
- **NFR-05:** When a class approaches 150 lines, split using **Mixin classes** — each Mixin handles exactly one concern, is small, focused, and independently testable
- **NFR-06:** Comments must explain **why** code is written the way it is, not just what it does; assumptions, edge cases, and design choices must be documented inline

### 8.2 Testing
- **NFR-07:** Global test coverage ≥ 85% (statement + branch)
- **NFR-08:** Every public function must have at least two tests: one for the normal (happy) path and one for the failure path
- **NFR-09:** All shared test fixtures must be defined in `tests/conftest.py` — duplicating fixtures across test files is forbidden
- **NFR-10:** Tests must not depend on live external services — Gemini API, Gmail, and MCP servers must be mocked
- **NFR-11:** A dedicated test (`test_file_size.py`) must automatically fail if any `src/` file exceeds 150 code lines
- **NFR-12:** Development follows TDD: Red → Green → Refactor
- **NFR-13:** Progressive sanity checks must validate the full pipeline at expanding grid sizes: 2×2 → 3×3 → 4×4 → 5×5, each as a dedicated integration test file

### 8.3 Security
- **NFR-14:** No secrets, API keys, or credential files may be committed to the repository
- **NFR-15:** `.env`, `.pem`, `.key`, and credential JSON files must be listed in `.gitignore`
- **NFR-16:** `.env-example` must exist with placeholder values for all required secrets
- **NFR-17:** MCP servers must enforce token-based authentication on every request (`401` on failure)
- **NFR-18:** Gmail credential JSON (`my_google.json`) must reside outside the project directory in a private folder (e.g., `~/private_google/`)

### 8.4 Configuration Management
- **NFR-19:** `pyproject.toml` is the single source of truth for dependencies, Ruff config, and pytest settings
- **NFR-20:** `uv.lock` must be committed and version-controlled
- **NFR-21:** All package operations use `uv` exclusively — `pip`, `python -m`, and `venv` are forbidden everywhere including scripts and CI/CD
- **NFR-22:** Configuration files must carry a `version` field starting at `1.00`

### 8.5 Architecture
- **NFR-23:** All external API calls (Gemini, Gmail) must route through the central API Gatekeeper (`src/api_gateway/gatekeeper.py`)
- **NFR-24:** The Gatekeeper must enforce rate limits (from `rate_limits.json`), queue requests (FIFO with configurable max depth), apply backpressure when queue is full, drain the queue when the rate window resets, retry on failure, and log all calls
- **NFR-25:** All business logic must be accessible through `GameSDK`; no business logic inside GUI, CLI, or any consumer layer
- **NFR-26:** Every `src/` subdirectory must be a proper Python package (`__init__.py` with `__all__`)
- **NFR-27:** All imports must use relative or package-based paths; absolute OS filesystem path manipulation is banned

### 8.6 Version Control & CI/CD
- **NFR-28:** The project must include a `src/version.py` file containing `VERSION = "1.00"`; this version must also appear in `pyproject.toml` and all `config/*.json` files
- **NFR-29:** The application must validate config file version compatibility at startup — if the loaded config version does not match the expected version, it must raise a clear error and exit
- **NFR-30:** A CI/CD pipeline must be implemented (e.g., GitHub Actions) that automatically runs tests and coverage on every commit using `uv run pytest tests/`; direct calls to `pytest` or `python -m pytest` are forbidden even in CI
- **NFR-31:** Git best practices must be followed throughout development: feature branches for each phase, pull requests before merging, meaningful commit messages, and tagged releases at each milestone
- **NFR-32:** A Prompt Engineering Log must be maintained (in `docs/PROMPT_LOG.md`) documenting every major prompt used during AI-assisted development — its purpose, example outputs, iterative improvements, and lessons learned

### 8.7 Edge Cases, Logging & Defensive Programming
- **NFR-33:** All edge cases must be identified in code comments, documented in the relevant mechanism PRD, and covered by dedicated tests
- **NFR-34:** All modules must include detailed logging (not just print statements) — log level, timestamp, and context must be included for every significant event
- **NFR-35:** Error handling must follow defensive programming principles: validate inputs before use, produce clear error messages, and degrade gracefully where possible (e.g., retry before raising)
- **NFR-36:** Expected test results must be documented: the test suite must produce a readable pass/fail report; logs from at least one successful and one failed run must be saved in `results/`

### 8.8 UI/UX
- **NFR-37:** The GUI must be evaluated against Nielsen's 10 usability heuristics before submission; findings must be documented in the README
- **NFR-38:** Interface documentation must include screenshots of every distinct GUI state, a description of the typical viewing workflow, and an accessibility note (color choices must convey meaning through text labels too, not color alone)

### 8.9 Research & Cost Analysis
- **NFR-39:** The project must include systematic parameter sensitivity analysis in `notebooks/results_analysis.ipynb` — at minimum: varying `visibility_radius` and `max_barriers`, measuring effect on cop win rate and average moves per sub-game
- **NFR-40:** Precise token accounting must be tracked per sub-game: input tokens, output tokens, cost per Gemini call, and total estimated cost for the full 6-game series; this must appear in the README cost section
- **NFR-41:** Budget management must be addressed: cost forecast at scale (e.g., 100 games), and the Gatekeeper must log token usage per call to support monitoring

### 8.10 Extensibility & ISO/IEC 25010
- **NFR-42:** The system must be designed for future extension without changing core logic — at minimum: swapping LLM provider via config, adding a new agent strategy without touching the orchestrator, adding a new MCP tool without modifying existing ones
- **NFR-43:** The system must align with all 8 ISO/IEC 25010 quality dimensions; compliance must be documented in `docs/PLAN.md` and `README.md`:

| Dimension | Implementation |
|-----------|---------------|
| Functional suitability | Game rules enforced by engine; all 6 sub-games complete correctly |
| Performance efficiency | Gatekeeper controls rate and concurrency; configurable timeouts; no unnecessary LLM calls |
| Compatibility | Config-driven MCP URLs allow integration with any external MCP server; SDK exposes standard interfaces |
| Usability | Nielsen's heuristics applied to GUI; interface documented with screenshots and workflows |
| Reliability | Technical failures trigger automatic reruns; gatekeeper retries with backoff |
| Security | Token auth on MCP servers; OAuth for Gmail; no secrets in repo; least-privilege API scopes |
| Maintainability | Modular structure; 150-line limit; SDK separation; TDD; zero lint violations; ADRs documented |
| Portability | Config-driven; no hardcoded OS paths; `uv` for reproducible environments across machines |

### 8.11 Concurrency & Thread Safety
- **NFR-44:** MCP servers handle concurrent incoming requests — shared state (message store, game state) must be protected with appropriate thread-safe mechanisms (e.g., locks or thread-safe data structures)
- **NFR-45:** The Gatekeeper queue must be thread-safe; concurrent LLM calls from both agents must not corrupt the queue or rate-limit counters

### 8.12 Performance
- **NFR-46:** The system must handle network latency to Render-hosted MCP servers gracefully (retry with configurable backoff from `rate_limits.json`)
- **NFR-47:** Sub-game reruns due to technical failure must be automatic — no user action required

---

## 9. Gmail API Integration — Setup Requirements

Based on instructor guidance, the following setup must be completed **before** coding the reporting module:

### Step 1 — Google Cloud Console
1. Create a new project at [Google Cloud Console](https://console.cloud.google.com/) using a **personal** Gmail account (not institutional). Name it in snake_case (e.g., `cops_robbers_007`).
2. Enable the **Gmail API** via the API Library.
3. Configure the **OAuth Consent Screen**: select External user type; fill in app name, support email, and developer contact email.
4. Add required OAuth scopes for Gmail (send, read drafts).
5. Create **OAuth 2.0 Client ID** credentials — select **Desktop App** as the application type.
6. Download the generated JSON file, rename it to `my_google.json`.
7. Move `my_google.json` to a private folder **outside** the project directory (e.g., `~/private_google/`).
8. Add your Gmail address (and all team members') as **Test Users** in the OAuth Consent Screen.

### Step 2 — Token Generation (first run only)
- `uv run` triggers a browser popup for OAuth login on first execution.
- Log in with the Gmail account registered as a Test User and grant permissions.
- A `token.json` file is generated in the same private external folder.
- Subsequent runs use the saved token without browser interaction.

### Step 3 — Environment Variables (in `.env`, never in source code)
```
GEMINI_API_KEY=your_gemini_api_key_here
COP_MCP_TOKEN=your_cop_token_here
THIEF_MCP_TOKEN=your_thief_token_here
GMAIL_CREDENTIALS_PATH=/path/to/private_google/my_google.json
GMAIL_TOKEN_PATH=/path/to/private_google/token.json
REPORT_RECIPIENT=rmisegal+uoh26b@gmail.com
```

### Step 4 — Email Rules
- Email body: **JSON only** — no subject text or free-form body content
- Triggered automatically via `GameSDK.send_report()` at end of game 6
- On send failure: retry via the Gatekeeper (max retries from `rate_limits.json`)

---

## 10. Assumptions

- The team uses **Gemini API** (free tier via Google AI Studio) — sufficient for 6 sub-games of up to 25 moves each
- The team has a personal Gmail account (not institutional) for OAuth setup
- The team deploys to **Render** (free tier) — no credit card required, 750 hours/month per service
- Internet access is available from the machine running the game engine (not behind a strict corporate firewall)
- The `token.json` OAuth token will be auto-refreshed by the Google API client library before expiry
- The Render service cold-start delay (30–60 sec) is acceptable since servers are called continuously during gameplay

---

## 11. Dependencies

| Dependency | Purpose | Notes |
|------------|---------|-------|
| FastMCP | MCP server framework | Core infrastructure |
| `google-generativeai` | Gemini LLM for agent reasoning | Free API key from Google AI Studio |
| Gmail API + Google API Client | Automated email reporting | OAuth2, personal account |
| `uv` | Package management and task runner | Mandatory; pip forbidden |
| Ruff | Linting | Zero violations required |
| pytest + pytest-cov | Testing | ≥ 85% coverage; TDD |
| pygame | GUI | Real-time board visualization |
| Render | MCP server hosting | Free tier; public HTTPS; no credit card |

---

## 12. Constraints

- No hardcoded values anywhere in `src/` — all from config or environment
- No file in `src/` may exceed 150 lines of code
- Agents must not transmit raw numeric coordinates in NL messages
- All package operations must use `uv` exclusively
- Gmail credentials must never be committed to the repository
- Sub-games that fail due to technical issues must be rerun automatically, not counted
- All consumer code (GUI, CLI) must access business logic only through `GameSDK`
- All imports must use relative or package-based paths — no `sys.path` manipulation
- Mixins must be used when class responsibilities would push a file over 150 lines

---

## 13. Out of Scope

- Reinforcement Learning / Q-table — optional extension, not required for grading
- Inter-group bonus competition — not implemented in this submission
- Support for board sizes larger than 5×5 in final evaluation
- Mobile or web-based GUI
- CLI interface (possible future extension via SDK, but not required)

---

## 14. Milestones

| Milestone | Deliverable | Phase |
|-----------|-------------|-------|
| M1 — Documentation Complete | `docs/PRD.md`, `docs/PLAN.md`, `docs/TODO.md`, all 5 dedicated PRDs approved | Phase 1 |
| M2 — Scaffolding & SDK | Project structure, `config.json`, `GameSDK` facade, `__init__.py` in all packages | Phase 2 |
| M3 — Game Engine + Fog of War | Core logic passes unit tests; `ObservedState` masks opponent; barriers enforced | Phase 3 |
| M4 — Local MCP Pipeline | Both servers running locally with token auth; 1 sub-game completes end-to-end | Phase 4–5 |
| M5 — Full Local Game Series | 6 valid sub-games complete locally; NL communication + NLP parser working | Phase 5–6 |
| M6 — Sanity Checks Pass | Pipeline validated at 2×2, 3×3, 4×4 before final 5×5 evaluation | Phase 11 |
| M7 — GUI + Cloud Deployment | GUI operational (SDK only); both MCP servers live on Render with token auth | Phase 8–9 |
| M8 — Automated Reporting | Gmail API sends JSON report automatically after game 6 | Phase 10 |
| M9 — Final Submission Ready | ≥ 85% coverage, zero lint violations, all checklist items satisfied, README complete | Phase 12–13 |
