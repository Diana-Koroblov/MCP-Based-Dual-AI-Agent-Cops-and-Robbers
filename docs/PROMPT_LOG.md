# Prompt Engineering Log
**Project:** Cops & Robbers — Dual AI Agent Pursuit via MCP Servers
**Version:** 1.00 | Updated throughout development

Every significant prompt used during AI-assisted development is logged here with purpose, example outputs, iterations, and lessons learned.

---

## Entry Format
```
### [PL-XX] — <Short title>
**Date:** YYYY-MM-DD
**Purpose:** What you were trying to achieve
**Context given to LLM:** (brief summary)
**Prompt:**
<exact prompt text>

**Example LLM output:**
<example response>

**Issues encountered:**
<what didn't work>

**Iterations:**
1. First version — problem observed
2. Fix applied — result

**Lessons learned:**
<what to reuse or avoid>
```

---

## Entries

### [PL-01] — Cop agent turn prompt (initial version)
**Date:** 2026-06-30
**Purpose:** Drive the Cop agent to select a move direction AND produce a natural-language message for the Thief — without ever including raw coordinates.
**Context given to LLM:** Agent role, current ObservedState (own position, known barriers, move count, fog-of-war visibility), last message received from the Thief, belief-state summary (most likely Thief position), list of valid moves.

**Prompt:**
```
You are the Cop in a Cops-and-Robbers pursuit game on a 5×5 grid.

Your current situation:
- Your position: {own_pos_description}  (e.g. "upper-left area")
- Move number: {move_count} of 25
- Barriers you have placed: {barriers_placed} of 5 remaining
- Thief visible: {opponent_visible}
- {opponent_description}  (e.g. "Thief is visible nearby to the southeast" OR "Thief is not visible")
- Your belief: the Thief is most likely in the {belief_region} area

Last message from Thief: "{received_message}"

Valid moves available: {valid_moves}  (e.g. N, NE, E, SE, S, SW, W, NW, PLACE_BARRIER)

Instructions:
1. Choose ONE action from the valid moves list.
2. Write a single sentence of natural language to send to the Thief as a bluff or warning.
3. NEVER include numeric coordinates (e.g. (3,2) or [1,4]) in your message.

Respond in exactly this format:
ACTION: <chosen action>
MESSAGE: <your natural-language message to the Thief>
```

**Example LLM output:**
```
ACTION: SE
MESSAGE: I can feel you cornered — there's nowhere left to run in this half of the board.
```

**Issues encountered:**
- Early version without the "NEVER include numeric coordinates" instruction caused the LLM to output messages like "I see you at (3,2)" — violating the free-form NL requirement.
- When the valid moves list was omitted, the LLM sometimes chose directions that were blocked by barriers.

**Iterations:**
1. Initial prompt with no coordinate restriction → LLM leaked coordinates in ~30% of outputs.
2. Added "NEVER include numeric coordinates" → coordinate leaks dropped to ~5%.
3. Added "valid moves available" list → LLM stopped choosing blocked directions.
4. Added positional descriptions in natural language (e.g. "upper-left area") instead of raw tuples → coordinate leaks reduced to 0% in testing.

**Lessons learned:**
- Explicitly forbidding coordinates in the instruction is necessary but not sufficient — also replace all coordinate references in the context with natural-language region descriptions.
- Providing the valid-moves list prevents the model from hallucinating impossible moves.
- The structured `ACTION: / MESSAGE:` response format makes parsing reliable and reduces NLP parser ambiguity.

---

### [PL-02] — Thief agent turn prompt (initial version)
**Date:** 2026-06-30
**Purpose:** Drive the Thief agent to select an evasive move AND produce a deceptive natural-language message — without exposing its real position.
**Context given to LLM:** Same structure as PL-01 but with the Thief role and no barriers_remaining field.

**Prompt:**
```
You are the Thief in a Cops-and-Robbers pursuit game on a 5×5 grid.
Your goal is to survive all 25 moves without being caught.

Your current situation:
- Your position: {own_pos_description}
- Move number: {move_count} of 25
- Cop visible: {opponent_visible}
- {opponent_description}
- Your belief: the Cop is most likely in the {belief_region} area

Last message from Cop: "{received_message}"

Valid moves available: {valid_moves}

Instructions:
1. Choose ONE action from the valid moves list.
2. Write a single sentence to send to the Cop — you may bluff, mislead, or taunt.
3. NEVER include numeric coordinates in your message.

Respond in exactly this format:
ACTION: <chosen action>
MESSAGE: <your natural-language message to the Cop>
```

**Example LLM output:**
```
ACTION: NW
MESSAGE: Keep looking to the east — I promise I'm nowhere near where you think I am.
```

**Issues encountered:**
- Same coordinate-leak issue as PL-01 before the explicit restriction was added.
- Thief occasionally chose PLACE_BARRIER (not a valid Thief action) when the list was unclear.

**Iterations:**
1. Added "Thief cannot place barriers" to the instructions explicitly.
2. Removed PLACE_BARRIER from the Thief's valid-moves list entirely.

**Lessons learned:**
- Role-specific valid-moves lists (no PLACE_BARRIER for Thief) prevent action-type confusion.
- The deception instruction ("you may bluff") produces richer NL messages and makes the game more interesting.

---

## PromptBuilder Template (Phase 5 implementation)

The following documents the exact structure produced by
`src/orchestrator/prompt_builder.PromptBuilder.build()`.

```
[ROLE SECTION]
You are the COP/THIEF in a grid pursuit game.
<Goal description>. The board is <rows> rows × <cols> columns.

[STATE SECTION]
Current state:
  • Turn: <N>
  • Your position: column <x>, row <y>
  • Barriers on board: <count>
  • Barriers you may still place: <count>   ← cop only, when > 0
  • Opponent VISIBLE at column <x>, row <y> ← when visible
  • Opponent NOT visible (fog of war).      ← when hidden

[MESSAGE SECTION]                           ← omitted if no prior message
Message from opponent: "<text>"

[BELIEF SECTION]
Your belief about the opponent's location: Most likely at column <x>,
row <y> (confidence <N>%)

[ACTIONS SECTION]
Valid actions this turn: N, NE, E, SE, S, SW, W, NW[, place_barrier]

[COORDINATE RESTRICTION — ALWAYS PRESENT]
CRITICAL: Never include numeric coordinates such as (x,y) or [x,y] in
your response. Describe positions using compass directions (N, S, E, W,
NE, NW, SE, SW) and relative terms (ahead, behind, left, right, far, close).

[OUTPUT FORMAT]
Respond with exactly two lines:
ACTION: <one of the valid actions listed above>
MESSAGE: <a short tactical message for your opponent (no coordinates)>
```

**Design decisions:**
- Belief summary replaces raw probability map — human-readable and avoids coordinate temptation.
- Opponent message quoted with typographic quotes to prevent prompt injection.
- Valid actions listed explicitly so the agent cannot hallucinate illegal moves.
- Coordinate restriction appears in every prompt regardless of role.
