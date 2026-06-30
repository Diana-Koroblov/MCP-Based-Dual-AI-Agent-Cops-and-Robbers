"""Tests for NLPParser — keyword extraction and coordinate-leak detection.

Assignment requirements:
* ≥ 10 diverse sample inputs tested.
* Zero instances of (x, y) or [x, y] numeric coordinates in any parsed output.
* All parsing results logged at DEBUG level (handled inside NLPParser).
"""

from __future__ import annotations

import pytest

from src.orchestrator.nlp_parser import NLPParser

_parser = NLPParser()

# ---------------------------------------------------------------------------
# 20 diverse NL inputs: explicit ACTION lines, free-text, tricky edge cases
# ---------------------------------------------------------------------------

_SAMPLES = [
    "ACTION: N\nMESSAGE: Heading north to cut off your escape.",
    "ACTION: SOUTH\nMESSAGE: Moving south — can't catch me!",
    "ACTION: east\nMESSAGE: I'll cut through the east corridor.",
    "ACTION: West\nMESSAGE: Blocking the western path.",
    "ACTION: NE\nMESSAGE: Closing in from the northeast.",
    "ACTION: northwest\nMESSAGE: Flanking via the northwest.",
    "ACTION: SE\nMESSAGE: Going southeast to corner you.",
    "ACTION: sw\nMESSAGE: Southwest is my escape route.",
    "ACTION: place_barrier\nMESSAGE: Placing a wall to block your route.",
    "ACTION: barrier\nMESSAGE: You won't get through here.",
    "Moving north — watch out!",
    "I think going east is the best tactical choice right now.",
    "The thief seems to be heading west — I'll cut them off.",
    "Dashing south toward the open edge to evade.",
    "Northeast! That's my move this turn.",
    "Heading northwest to the open corner.",
    "I'll place a barrier here to block the corridor.",
    "Evasion plan: southwest diagonal.",
    "Cop is closing in — dashing east!",
    "Lost track, maybe west is safest?",
]


# ---------------------------------------------------------------------------
# Coordinate-leak check: raw_text must never contain (x, y) or [x, y]
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text", _SAMPLES)
def test_no_coordinate_leak_in_raw_text(text):
    """Parsed raw_text must never contain forbidden numeric coordinates."""
    result = _parser.parse(text)
    assert not NLPParser.has_coordinate_leak(result.raw_text), (
        f"Coordinate leak detected in raw_text: {result.raw_text!r}"
    )


# ---------------------------------------------------------------------------
# target_cell is always None (coordinates are forbidden in LLM output)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text", _SAMPLES)
def test_target_cell_always_none(text):
    assert _parser.parse(text).target_cell is None


# ---------------------------------------------------------------------------
# Direction extraction — ACTION: line takes priority
# ---------------------------------------------------------------------------

def test_parse_north():
    r = _parser.parse("ACTION: N\nMESSAGE: Going north.")
    assert r.direction is not None and r.direction.value == "N"
    assert r.confidence >= 0.5


def test_parse_south():
    r = _parser.parse("ACTION: SOUTH\nMESSAGE: South.")
    assert r.direction is not None and r.direction.value == "S"


def test_parse_east():
    r = _parser.parse("ACTION: east\nMESSAGE: East!")
    assert r.direction is not None and r.direction.value == "E"


def test_parse_west():
    r = _parser.parse("ACTION: West\nMESSAGE: West.")
    assert r.direction is not None and r.direction.value == "W"


def test_parse_ne():
    r = _parser.parse("ACTION: NE\nMESSAGE: Northeast.")
    assert r.direction is not None and r.direction.value == "NE"


def test_parse_nw():
    r = _parser.parse("ACTION: northwest\nMESSAGE: Northwest.")
    assert r.direction is not None and r.direction.value == "NW"


def test_parse_se():
    r = _parser.parse("ACTION: SE\nMESSAGE: Southeast.")
    assert r.direction is not None and r.direction.value == "SE"


def test_parse_sw():
    r = _parser.parse("ACTION: sw\nMESSAGE: Southwest.")
    assert r.direction is not None and r.direction.value == "SW"


# ---------------------------------------------------------------------------
# place_barrier detection
# ---------------------------------------------------------------------------

def test_parse_place_barrier_explicit():
    r = _parser.parse("ACTION: place_barrier\nMESSAGE: Blocking.")
    assert r.action == "place_barrier"
    assert r.direction is None
    assert r.confidence >= 0.5


def test_parse_barrier_keyword():
    r = _parser.parse("ACTION: barrier\nMESSAGE: Wall up.")
    assert r.action == "place_barrier"


# ---------------------------------------------------------------------------
# Message extraction
# ---------------------------------------------------------------------------

def test_message_extracted_correctly():
    r = _parser.parse("ACTION: N\nMESSAGE: Hello from the north.")
    assert r.message == "Hello from the north."


def test_no_message_line_gives_empty_string():
    r = _parser.parse("Going north at full speed.")
    assert r.message == ""


# ---------------------------------------------------------------------------
# Low confidence when nothing recognised
# ---------------------------------------------------------------------------

def test_unrecognised_text_gives_low_confidence():
    r = _parser.parse("I am very confused about what to do next.")
    assert r.confidence < 0.5
    assert r.action is None
    assert r.direction is None


# ---------------------------------------------------------------------------
# has_coordinate_leak — static method
# ---------------------------------------------------------------------------

def test_has_coordinate_leak_detects_parens():
    assert NLPParser.has_coordinate_leak("Move to (3, 2) quickly.") is True


def test_has_coordinate_leak_detects_brackets():
    assert NLPParser.has_coordinate_leak("Head to [1, 4].") is True


def test_has_coordinate_leak_clean_text():
    assert NLPParser.has_coordinate_leak("Go north, then east.") is False
