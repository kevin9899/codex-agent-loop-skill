from __future__ import annotations

import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "record_resume_event.py"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")


def read_latest_resume_event(run_dir: Path) -> str:
    resume_dir = run_dir / "resume-events"
    events = sorted(resume_dir.glob("*-resume.md"))
    if not events:
        raise AssertionError("no resume event was written")
    return events[-1].read_text(encoding="utf-8")


class RecordResumeEventTests(unittest.TestCase):
    def run_script(self, run_dir: Path) -> str:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), str(run_dir), "--trigger", "any_followup_message"],
            check=True,
            capture_output=True,
            text=True,
        )
        return completed.stdout.strip()

    def test_records_matching_continue_receipt_for_current_closeout_round(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            write_text(
                run_dir / "handoff.md",
                """
                # Handoff
                - `run_decision`: `continue`
                - `host_resume_mode`: `same_turn_only`
                - `closeout_round_id`: `round-current`
                - `next_mandatory_action`: `collect fresh verdicts`
                """,
            )
            write_text(
                run_dir / "closeout-receipts" / "20260424T010000Z-continue.md",
                """
                # Closeout Receipt
                - `closeout_round_id`: `round-older`
                """,
            )
            write_text(
                run_dir / "closeout-receipts" / "20260424T000000Z-continue.md",
                """
                # Closeout Receipt
                - `closeout_round_id`: `round-current`
                """,
            )

            self.run_script(run_dir)
            event_text = read_latest_resume_event(run_dir)

            self.assertIn(
                "previous_continue_receipt: closeout-receipts/20260424T000000Z-continue.md",
                event_text,
            )
            self.assertIn("previous_continue_receipt_alignment: matched_closeout_round", event_text)

    def test_records_none_when_no_matching_continue_receipt_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            write_text(
                run_dir / "handoff.md",
                """
                # Handoff
                - `run_decision`: `continue`
                - `host_resume_mode`: `same_turn_only`
                - `closeout_round_id`: `round-current`
                - `next_mandatory_action`: `collect fresh verdicts`
                """,
            )
            write_text(
                run_dir / "closeout-receipts" / "20260424T010000Z-continue.md",
                """
                # Closeout Receipt
                - `closeout_round_id`: `round-older`
                """,
            )

            self.run_script(run_dir)
            event_text = read_latest_resume_event(run_dir)

            self.assertIn("previous_continue_receipt: none", event_text)
            self.assertIn(
                "previous_continue_receipt_alignment: no_matching_continue_receipt_for_current_closeout_round",
                event_text,
            )


if __name__ == "__main__":
    unittest.main()
