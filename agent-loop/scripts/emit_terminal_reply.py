#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from terminal_reply_summary import build_stop_reply_lines
from validate_handoff import clean_value, flatten_multivalue_text, parse_handoff


def require_gate_call(run_dir: Path) -> int:
    if os.environ.get("AGENT_LOOP_CLOSEOUT_GATE") != "1":
        print("emit_terminal_reply.py is internal; use closeout_gate.py", file=sys.stderr)
        return 1
    gate_run_dir = os.environ.get("AGENT_LOOP_GATE_RUN_DIR", "")
    if not gate_run_dir or Path(gate_run_dir).resolve() != run_dir:
        print("emit_terminal_reply.py requires AGENT_LOOP_GATE_RUN_DIR to match the target run dir", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render and validate the low-freedom stop/planning_complete reply from handoff.md.",
    )
    parser.add_argument("run_dir", help="Path to the agent-loop run directory")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    gate_error = require_gate_call(run_dir)
    if gate_error:
        return gate_error
    handoff_path = run_dir / "handoff.md"
    if not handoff_path.exists():
        print(f"handoff.md not found: {handoff_path}", file=sys.stderr)
        return 1

    fields = parse_handoff(handoff_path)
    run_decision = clean_value(str(fields.get("run_decision", "")))
    if run_decision not in {"stop", "planning_complete"}:
        print("emit_terminal_reply.py requires handoff.md with run_decision=stop|planning_complete", file=sys.stderr)
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

    if run_decision == "stop":
        reply_lines = build_stop_reply_lines(fields, run_dir)
    else:
        reply_lines = [
            f"loop_state={clean_value(str(fields.get('loop_state', '')))}",
            f"run_decision={run_decision}",
            f"current_or_next_stage={clean_value(str(fields.get('current_or_next_stage', '')))}",
            f"stop_reason={clean_value(str(fields.get('pause_reason', '')))}",
            f"external_authority_basis={clean_value(str(fields.get('external_authority_basis', '')))}",
            f"resume_instructions={flatten_multivalue_text(fields.get('resume_instructions', '')).replace('`', '')}",
        ]

    reply = "\n".join(reply_lines) + "\n"

    validator = Path(__file__).with_name("validate_terminal_reply.py")
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

    sys.stdout.write(reply)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
