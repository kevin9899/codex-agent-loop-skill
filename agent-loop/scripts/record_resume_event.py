#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

from validate_handoff import clean_value, extract_artifact_field, parse_handoff


def continue_receipts(run_dir: Path) -> list[Path]:
    receipt_dir = run_dir / "closeout-receipts"
    if not receipt_dir.exists():
        return []
    return sorted(
        receipt_dir.glob("*-continue.md"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )


def matching_continue_receipt(run_dir: Path, closeout_round_id: str) -> Path | None:
    if not closeout_round_id:
        return None
    for receipt in continue_receipts(run_dir):
        text = receipt.read_text(encoding="utf-8", errors="ignore")
        if clean_value(extract_artifact_field(text, "closeout_round_id")) == closeout_round_id:
            return receipt
    return None


def previous_continue_receipt_metadata(run_dir: Path, closeout_round_id: str) -> tuple[Path | None, str]:
    matching_receipt = matching_continue_receipt(run_dir, closeout_round_id)
    if matching_receipt is not None:
        return matching_receipt, "matched_closeout_round"
    if continue_receipts(run_dir):
        return None, "no_matching_continue_receipt_for_current_closeout_round"
    return None, "no_continue_receipt_available"


def rel_or_name(path: Path | None, run_dir: Path) -> str:
    if path is None:
        return "none"
    try:
        return path.relative_to(run_dir).as_posix()
    except ValueError:
        return str(path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Record that a same-turn-only continue receipt was resumed by a follow-up message.",
    )
    parser.add_argument("run_dir", help="Path to the agent-loop run directory")
    parser.add_argument(
        "--trigger",
        default="any_followup_message",
        help="Short trigger label for the resume event",
    )
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    handoff_path = run_dir / "handoff.md"
    if not handoff_path.exists():
        print(f"handoff.md not found: {handoff_path}")
        return 1

    fields = parse_handoff(handoff_path)
    run_decision = clean_value(str(fields.get("run_decision", "")))
    host_resume_mode = clean_value(str(fields.get("host_resume_mode", "")))
    closeout_round_id = clean_value(str(fields.get("closeout_round_id", "")))
    next_action = clean_value(str(fields.get("next_mandatory_action", "")))
    previous_receipt, previous_receipt_alignment = previous_continue_receipt_metadata(run_dir, closeout_round_id)

    if run_decision != "continue":
        print("record_resume_event.py requires handoff.md with run_decision=continue")
        return 1

    if host_resume_mode != "same_turn_only":
        print("record_resume_event.py is only needed for host_resume_mode=same_turn_only")
        return 1

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    event_dir = run_dir / "resume-events"
    event_dir.mkdir(parents=True, exist_ok=True)
    event_path = event_dir / f"{timestamp}-resume.md"

    event_path.write_text(
        "\n".join(
            [
                "resume_event_version: v1",
                f"resume_event_id: {timestamp}-resume",
                f"trigger: {clean_value(args.trigger)}",
                f"run_decision_at_resume: {run_decision}",
                f"host_resume_mode: {host_resume_mode}",
                f"closeout_round_id: {closeout_round_id}",
                f"previous_continue_receipt: {rel_or_name(previous_receipt, run_dir)}",
                f"previous_continue_receipt_alignment: {previous_receipt_alignment}",
                "root_cause: same_turn_only host made the previous continue receipt visible as a final turn boundary and did not keep background execution alive",
                "resume_decision: continue_immediately_without_permission_prompt",
                f"next_mandatory_action: {next_action}",
                "stop_status: not_stopped",
                "host_boundary_effect: visible_turn_only_not_goal_stop",
                "auto_resume_trigger: any_followup_message",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(event_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
