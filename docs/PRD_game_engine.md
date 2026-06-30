# PRD: Game Engine Mechanism
**Version:** 1.00 | Part of: Cops & Robbers MCP Assignment

---

## 1. Description

The game engine is the central logic layer that manages the board, enforces all game rules, applies the fog-of-war filter, sequences turns, detects win/loss conditions, and runs the complete 6-sub-game series without manual intervention. It is the single source of truth for game state.

---

## 2. Theoretical Background

The pursuit game is modeled as a **Decentralized Partially Observable Markov Decision Process (Dec-POMDP)**. The state space is the set of all combinations of (cop_position, thief_position, barrier_locations). Each agent receives a partial observation (ObservedState) rather than the full state, making this a partially observable problem. The game terminates per sub-game when a terminal condition is met (capture or move limit), and results are accumulated across 6 episodes.

---

## 3. Inputs

| Input | Type | Source |
|-------|------|--------|
| `grid_size` | `[int, int]` | `config.json` |
| `max_moves` | `int` | `config.json` |
| `num_games` | `int` | `config.json` |
| `max_barriers` | `int` | `config.json` |
| `visibility_radius` | `int` | `config.json` |
| `scoring` | `dict` | `config.json` |
| Agent action each turn | `Action` enum | Orchestrator via `GameSDK` |

---

## 4. Outputs

| Output | Type | Consumer |
|--------|------|----------|
| `ObservedState` per agent per turn | `ObservedState` dataclass | Orchestrator |
| `SubGameResult` after each sub-game | `SubGameResult` dataclass | Scorer, Reporting |
| Cumulative score totals | `ScoreSummary` dataclass | `GameSDK`, Reporting |
| Win/loss event | `str` ("cop" / "thief" / "technical_failure") | `full_game.py` |

---

## 5. Rules and Constraints

- Board size is configurable; default 5×5; no hardcoded dimensions anywhere
- Thief always moves first each turn; Cop moves second
- Movement allowed in 8 directions (N, NE, E, SE, S, SW, W, NW)
- Cop may place a barrier on its current cell instead of moving (uses 1 turn, cop does not move)
- Hard barrier limit: exactly 5 per Cop per sub-game; a 6th attempt must be rejected and logged
- Barriers are impassable for both agents immediately after placement; cannot be overwritten
- Barriers reset between sub-games; positions reset to initial configuration
- Cop wins sub-game: cop_pos == thief_pos
- Thief wins sub-game: survives all `max_moves` turns without cop entering its cell
- Technical failure: sub-game is invalid, automatically rerun; not counted toward the 6
- Fog of war: each agent receives `ObservedState`, never `GameState`; opponent visible only within `visibility_radius` cells (Chebyshev distance)

---

## 6. Fog of War — ObservedState Specification

```python
@dataclass(frozen=True)
class ObservedState:
    own_pos: tuple[int, int]
    known_barriers: frozenset[tuple[int, int]]
    opponent_visible: bool
    opponent_pos_if_visible: tuple[int, int] | None  # None if not visible
    move_count: int
    barriers_remaining: int  # cop only; always 0 for thief
```

The `fog_of_war.py` module applies this filter before any state is passed to the Orchestrator. The engine never passes `GameState` directly to agents.

---

## 7. Performance Expectations

- Each turn (including fog-of-war filtering) must complete in < 1 ms (pure Python, no I/O)
- Sub-game reruns must be automatic with no latency beyond the failed turn detection
- Scorer must handle 6 accumulated results in O(1)

---

## 8. Alternatives Considered

| Alternative | Reason rejected |
|-------------|----------------|
| Full observability (agents see entire board) | Violates assignment requirement; eliminates the NL communication challenge |
| Circular visibility radius | Chebyshev distance chosen — simpler to compute on a grid, consistent with 8-direction movement |
| Random rerun delay on technical failure | No delay needed; failure is detected immediately and rerun is instant |

---

## 9. Success Criteria and Test Scenarios

| Scenario | Expected result |
|----------|----------------|
| Cop moves onto thief's cell | Sub-game ends: cop wins; scores updated |
| Thief survives 25 moves | Sub-game ends: thief wins; scores updated |
| Cop attempts 6th barrier | Action rejected; move not consumed; error logged |
| Agent requests `ObservedState` with opponent 3 cells away (radius=2) | `opponent_visible = False`, `opponent_pos_if_visible = None` |
| Agent requests `ObservedState` with opponent 1 cell away (radius=2) | `opponent_visible = True`, correct position returned |
| Technical failure mid-sub-game | Sub-game invalidated; new sub-game starts automatically |
| Full 6-game series runs | `full_game.py` returns `ScoreSummary` with accumulated totals; no manual step |
