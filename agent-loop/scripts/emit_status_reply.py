#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from validate_handoff import clean_value, flatten_multivalue_text, is_noneish, parse_handoff


def handoff_digest(handoff_path: Path) -> str:
    return hashlib.sha256(handoff_path.read_bytes()).hexdigest()


def persist_status_receipt(run_dir: Path, body: str) -> None:
    receipts_dir = run_dir / "status-receipts"
    receipts_dir.mkdir(parents=True, exist_ok=True)
    handoff_path = run_dir / "handoff.md"
    fields = parse_handoff(handoff_path)
    receipt_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-status")
    receipt = "\n".join(
        [
            "# Status Receipt",
            "",
            f"- `receipt_id`: {receipt_id}",
            f"- `handoff_digest`: {handoff_digest(handoff_path)}",
            f"- `run_decision`: {clean_value(str(fields.get('run_decision', '')))}",
            f"- `closeout_round_id`: {clean_value(str(fields.get('closeout_round_id', '')))}",
            "- `rendered_reply`:",
            "```text",
            body.rstrip(),
            "```",
            "",
        ]
    )
    (receipts_dir / f"{receipt_id}.md").write_text(receipt, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render and validate the low-freedom live-state status reply from handoff.md.",
    )
    parser.add_argument("run_dir", help="Path to the agent-loop run directory")
    parser.add_argument(
        "--blocking-or-risk",
        help="Optional explicit blocker/risk override. Defaults to handoff blocking_findings when concrete.",
    )
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    handoff_path = run_dir / "handoff.md"
    if not handoff_path.exists():
        print(f"handoff.md not found: {handoff_path}", file=sys.stderr)
        return 1

    fields = parse_handoff(handoff_path)
    run_decision = clean_value(str(fields.get("run_decision", "")))
    if run_decision != "continue":
        print("emit_status_reply.py requires handoff.md with run_decision=continue", file=sys.stderr)
        return 1
    if clean_value(str(fields.get("host_resume_mode", ""))) == "same_turn_only":
        print("emit_status_reply.py may not be used when host_resume_mode=same_turn_only", file=sys.stderr)
        return 1

    handoff_validator = Path(__file__).with_name("validate_handoff.py")
    handoff_result = subprocess.run(
        [sys.executable, str(handoff_validator), str(run_dir), "--require-consensus"],
        text=True,
        capture_output=True,
    )
    if handoff_result.returncode != 0:
        if handoff_result.stdout:
            sys.stderr.write(handoff_result.stdout)
        if handoff_result.stderr:
            sys.stderr.write(handoff_result.stderr)
        return handoff_result.returncode

    lines = [
        f"loop_state={clean_value(str(fields.get('loop_state', '')))}",
        f"current_or_next_stage={clean_value(str(fields.get('current_or_next_stage', '')))}",
        f"next_mandatory_action={clean_value(str(fields.get('next_mandatory_action', '')))}",
    ]

    blocking_or_risk = clean_value(args.blocking_or_risk or "")
    if not blocking_or_risk:
        candidate = flatten_multivalue_text(fields.get("blocking_findings", ""))
        if not is_noneish(candidate):
            blocking_or_risk = candidate
    if blocking_or_risk:
        lines.append(f"blocking_or_risk={blocking_or_risk}")

    reply = "\n".join(lines) + "\n"

    validator = Path(__file__).with_name("validate_status_reply.py")
    result = subprocess.run(
        [sys.executable, str(validator), "--run-dir", str(run_dir)],
        input=reply,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        if result.stdout:
            sys.stderr.write(result.stdout)
        if result.stderr:
            sys.stderr.write(result.stderr)
        return result.returncode

    persist_status_receipt(run_dir, reply)
    sys.stdout.write(reply)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
