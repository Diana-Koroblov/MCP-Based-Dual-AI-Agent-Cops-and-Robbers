"""Reporting mixin for GameSDK.

Why a mixin: the SDK facade would exceed 150 lines if reporting logic were
inlined. Extracting it here keeps both files focused and testable in isolation.
"""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)


class ReportingMixin:
    """Mixin that adds send_report() to GameSDK."""

    def send_report(self, sub_game_results: list, llm_usage: dict) -> None:
        """Build a JSON report from completed sub-games and send it via Gmail.

        Args:
            sub_game_results: List of SubGameResult dataclasses (exactly 6).
            llm_usage: Dict with keys total_input_tokens, total_output_tokens,
                       estimated_cost_usd from the Gatekeeper token log.

        Raises:
            ValueError: if sub_game_results does not contain exactly 6 entries.
            RuntimeError: if the Gmail send fails after all retries.
        """
        if len(sub_game_results) != 6:  # noqa: PLR2004
            raise ValueError(
                f"Expected exactly 6 sub-game results, got {len(sub_game_results)}"
            )
        # Import here to avoid circular imports at module load time.
        from src.reporting.gmail_sender import GmailSender
        from src.reporting.json_builder import JsonReportBuilder

        config = getattr(self, "_config", {})
        report_json = JsonReportBuilder(config).build(sub_game_results, llm_usage)
        GmailSender(config).send(report_json)
        log.info("Report sent successfully.")
