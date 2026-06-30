# PRD: NLP Communication Mechanism
**Version:** 1.00 | Part of: Cops & Robbers MCP Assignment

---

## 1. Description

Agents communicate exclusively through free-form natural language — never through rigid coordinate protocols. The NLP Communication mechanism covers: (1) prompt design that drives agents to produce NL output, (2) an NLP parser that extracts actionable intentions from that text, (3) a belief state that aggregates spatial inferences across turns, and (4) enforcement that raw coordinates never appear in messages.

---

## 2. Theoretical Background

In a Dec-POMDP setting with partial observability, agents cannot rely on ground-truth state exchange. Instead, they must communicate intent under ambiguity. Natural language is inherently ambiguous — phrases like "I'm heading north" can mean many things depending on context. The receiving agent must use Bayesian-style belief updating to maintain a probability distribution over the opponent's likely position, combining:
- Direct visibility (from `ObservedState`)
- Spatial inferences from NL messages (e.g., "I'm in the lower half" → higher probability on rows 3–4)
- Prior position from the previous turn

---

## 3. Message Format Rules

### Permitted (free-form NL)
- `"I'm closing in from the northwest — you're running out of room."`
- `"I just blocked the eastern corridor. Your escape route is shrinking."`
- `"I could be anywhere in the lower half of the board by now."`
- Deception is explicitly permitted: agents may lie about their position or intentions

### Forbidden (raw coordinates)
- `"I am at (3, 2)"` — numeric coordinate tuple
- `"Move to cell [4, 1]"` — bracketed coordinates
- `"x=3, y=2"` — named coordinate format
- Any message matching the regex `\(\d+,\s*\d+\)` or `\[\d+,\s*\d+\]`

A test (`test_nlp_parser.py`) must assert that no generated agent message matches the forbidden patterns.

---

## 4. NLP Parser (`nlp_parser.py`)

The parser receives raw LLM text output and extracts the agent's intended action.

### Input
Raw natural-language string from the LLM.

### Output
```python
@dataclass
class IntentionResult:
    action: str           # "move" | "place_barrier" | "hold"
    direction: str | None # "north" | "northeast" | ... | None
    target_cell: tuple[int, int] | None  # resolved on board; None if ambiguous
    confidence: float     # 0.0–1.0
    raw_text: str         # original message for logging
```

### Parsing strategy
1. Keyword matching for direction words (north, south, east, west, diagonal variants)
2. Action keyword detection (place, block, barrier → `place_barrier`; move, head, go → `move`)
3. If ambiguous (confidence < 0.5): fall back to the strategy module's heuristic recommendation
4. Log every parse result at DEBUG level with raw text and extracted intention

### Edge cases
- Agent says "I'm staying put" → `action = "hold"` (Thief cannot hold; treated as random valid move)
- Agent message contains no spatial information → belief state unchanged; strategy chooses action
- LLM produces empty output → treated as technical failure; triggers sub-game rerun

---

## 5. Belief State (`belief_state.py`)

Maintains a probability distribution over all cells for the opponent's location.

### Update rules (each turn)
1. **Direct observation:** if `opponent_visible = True` in `ObservedState`, set probability 1.0 at that cell, 0.0 elsewhere
2. **NL inference:** parse spatial keywords from received message; boost probability of cells matching the description
3. **Movement prior:** apply a diffusion kernel — opponent is more likely to have moved to adjacent cells than to have teleported
4. **Barrier elimination:** set probability 0.0 for all barrier cells

### Output
- `most_likely_pos() → tuple[int, int]` — highest-probability cell
- `probability_map() → dict[tuple, float]` — full distribution for strategy use

---

## 6. Prompt Design

Each agent's system prompt must include:
- Role description (Cop or Thief)
- Current `ObservedState` (own position, known barriers, move count, visibility)
- Received NL message from opponent (if any)
- Belief state summary (most likely opponent location)
- List of valid actions available this turn
- Explicit instruction: **"Respond with a natural-language message to your opponent AND a chosen action. Never include numeric coordinates in your message."**

Prompt templates are maintained in `prompt_builder.py` and logged in `docs/PROMPT_LOG.md`.

---

## 7. Inputs

| Input | Source |
|-------|--------|
| `ObservedState` | `fog_of_war.py` via `GameSDK` |
| Opponent's NL message | `receive_message()` tool on MCP server |
| Previous belief state | `belief_state.py` (persisted across turns) |
| LLM response (raw text) | Gemini API via Gatekeeper |

---

## 8. Outputs

| Output | Consumer |
|--------|----------|
| NL message to send | `send_message()` tool on MCP server |
| `IntentionResult` | `client.py` → tool invocation |
| Updated belief state | Strategy module |

---

## 9. Performance Expectations

- NLP parsing must complete in < 100 ms (no external calls; pure text processing)
- Belief state update must complete in < 10 ms for a 5×5 grid (25 cells)

---

## 10. Alternatives Considered

| Alternative | Reason rejected |
|-------------|----------------|
| Structured JSON messages with coordinates | Violates assignment requirement; eliminates the NL challenge |
| Regex-only NLP parser | Too brittle for diverse LLM outputs; keyword + heuristic hybrid is more robust |
| Neural NLP model for parsing | Overkill for this domain; adds latency and dependencies |

---

## 11. Success Criteria and Test Scenarios

| Scenario | Expected result |
|----------|----------------|
| Message: "heading northeast" | `action=move`, `direction=northeast`, `confidence>0.7` |
| Message: "placing a wall here" | `action=place_barrier`, `confidence>0.8` |
| Message: "(3, 2)" | Forbidden pattern detected; test fails (coordinate leak) |
| Empty LLM output | Technical failure triggered; sub-game reruns |
| Opponent says "I'm in the south" | Belief state probability boosted for rows 3–4 |
| Opponent position within radius | Belief state set to 1.0 at that cell |
