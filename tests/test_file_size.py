"""Automated file-size guard.

Why this test exists: the Global Mandate requires every src/ Python file to
stay under 150 lines. This test enforces that constraint automatically on every
CI run, so a developer can't accidentally merge an oversized module.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_SRC_ROOT = Path(__file__).parent.parent / "src"
_MAX_LINES = 150


def _collect_python_files() -> list[Path]:
    return sorted(_SRC_ROOT.rglob("*.py"))


@pytest.mark.parametrize("py_file", _collect_python_files())
def test_file_within_150_lines(py_file: Path) -> None:
    """Each src/ Python file must not exceed 150 lines of code."""
    lines = py_file.read_text(encoding="utf-8").splitlines()
    line_count = len(lines)
    assert line_count <= _MAX_LINES, (
        f"{py_file.relative_to(_SRC_ROOT.parent)} has {line_count} lines "
        f"(limit: {_MAX_LINES}). Refactor by extracting Mixins or Helpers."
    )
