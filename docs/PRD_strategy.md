# PRD: Agent Strategy Mechanism
**Version:** 1.00 | Part of: Cops & Robbers MCP Assignment

---

## 1. Description

The strategy module provides decision-making logic for both agents — determining which action to take each turn based on the agent's `ObservedState` and `belief_state`. The default implementation uses Manhattan-distance heuristics. Reinforcement Learning (Q-table) is documented here as an optional extension.

---

## 2. Theoretical Background

Since RL is not a prerequisite for this course, the primary approach is **heuristic decision-making** using Manhattan distance as a proxy for board proximity. Manhattan distance between two cells (x1,y1) and (x2,y2) is |x1-x2| + |y1-y2|. The cop minimizes this distance to the estimated thief position; the thief maximizes it.

For the optional Q-Learning extension: a Q-table maps (state, action) pairs to expected cumulative rewards, updated via the Bellman equation after each move. The epsilon-greedy policy balances exploration and exploitation.

---

## 3. Heuristic Strategy (Default — Required)

### Cop (`heuristic_cop.py`)

**Goal:** minimize distance to estimated thief position; use barriers to reduce thief's escape options.

**Action selection:**
1. Get `most_likely_pos()` from `belief_state`
2. Evaluate all 8 valid neighboring cells + barrier placement
3. Move to the neighbor that minimizes Manhattan distance to estimated thief pos
4. Place a barrier if: barriers remaining > 0 AND a barrier at current cell would block a high-probability escape corridor (thief's most likely direction of movement)
5. If all neighbors are blocked: hold (rare edge case; log at WARNING level)

### Thief (`heuristic_thief.py`)

**Goal:** maximize distance to estimated cop position; avoid corners.

**Action selection:**
1. Get `most_likely_pos()` from `belief_state`
2. Evaluate all 8 valid neighboring cells
3. Move to the neighbor that maximizes Manhattan distance from estimated cop pos
4. Tie-breaking: prefer cells away from board corners (corner cells have fewer escape options)
5. If all neighbors are blocked: hold (edge case; logged)

---

## 4. Optional Extension: Tabular Q-Learning

> Not required for grading. Implement only if time permits after core submission is complete.

### State representation
```python
state = (own_pos, estimated_opponent_pos, tuple(sorted(barriers)))
```

### Action space
- Cop: 8 directional moves + `place_barrier` = 9 actions
- Thief: 8 directional moves = 8 actions

### Reward function

| Event | Cop reward | Thief reward |
|-------|-----------|-------------|
| Each move taken | -0.1 (fuel cost) | -0.1 |
| Cop captures thief | +10.0 | -10.0 |
| Thief survives 25 moves | -5.0 | +5.0 |
| Invalid move attempted | -1.0 | -1.0 |

### Bellman update
```
Q(s,a) ← Q(s,a) + α [ r + γ·max_a' Q(s',a') − Q(s,a) ]
```
- α (learning rate): 0.1 (configurable in `config.json`)
- γ (discount factor): 0.9
- ε (exploration): starts at 1.0, decays by 0.995 per episode, floor at 0.01

---

## 5. Inputs

| Input | Source |
|-------|--------|
| `ObservedState` | `fog_of_war.py` via `GameSDK` |
| `BeliefState` (probability map) | `belief_state.py` |
| Board size and barrier locations | `config.json` |
| `barriers_remaining` (cop only) | `ObservedState` |

---

## 6. Outputs

| Output | Type | Consumer |
|--------|------|----------|
| Chosen action | `Action` enum | `nlp_parser.py` / `client.py` |
| Action confidence | `float` | `prompt_builder.py` (used in prompt context) |

---

## 7. Performance Expectations

- Heuristic decision must complete in < 5 ms for a 5×5 grid
- Q-table lookup (if used) must complete in < 1 ms

---

## 8. Alternatives Considered

| Alternative | Reason rejected |
|-------------|----------------|
| Random action selection | Produces uninteresting games; demonstrates no strategy |
| Minimax search | Requires full board knowledge; incompatible with partial observability |
| Deep Q-Network (DQN) | Overkill; RL is not a course prerequisite; tabular Q-learning is the recommended lightweight RL approach |
| A* pathfinding | Assumes full knowledge of opponent position; incompatible with fog of war |

---

## 9. Success Criteria and Test Scenarios

| Scenario | Expected result |
|----------|----------------|
| Cop directly adjacent to thief (visible) | Cop moves onto thief's cell; sub-game ends |
| Cop has 0 barriers remaining | `place_barrier` action never selected |
| All Cop neighbors blocked | Action = hold; WARNING logged |
| Thief in corner with cop approaching | Thief moves away from corner toward open area |
| Heuristic vs. random opponent over 6 games | Heuristic cop achieves at least 3 wins (informal benchmark) |
