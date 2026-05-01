#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from validate_handoff import clean_value, is_noneish, parse_handoff


def render_field_value(value: object) -> str:
    return clean_value(str(value)).replace("`", "")


def render_resume_instructions(value: object) -> str:
    if isinstance(value, list):
        parts = [render_field_value(item) for item in value if clean_value(str(item))]
        return " | ".join(parts)
    return render_field_value(value)


def render_resume_command(run_dir: Path) -> str:
    return f"$loop {run_dir.as_posix()}"


def render_pause_scope(external_authority_basis: object) -> str:
    basis = render_field_value(external_authority_basis)
    if basis == "host_turn_boundary":
        return "host_boundary_only"
    if basis == "explicit_user_pause":
        return "explicit_pause"
    if basis == "explicit_user_redirect":
        return "redirected"
    if basis == "human_decision_required":
        return "human_decision_gate"
    return "general_pause"


def render_continuation_authority(external_authority_basis: object) -> str:
    basis = render_field_value(external_authority_basis)
    if basis == "host_turn_boundary":
        return "standing"
    if basis in {"explicit_user_pause", "explicit_user_redirect", "explicit_user_stop"}:
        return "withheld_by_user"
    if basis == "human_decision_required":
        return "blocked_pending_human"
    return "standing"


def render_semantic_state(external_authority_basis: object) -> str:
    basis = render_field_value(external_authority_basis)
    if basis == "host_turn_boundary":
        return "incomplete_forced_boundary"
    if basis in {"explicit_user_pause", "explicit_user_redirect"}:
        return "incomplete_paused_by_authority"
    if basis == "human_decision_required":
        return "incomplete_blocked_pending_human"
    return "incomplete_paused"


def render_followup_resume_policy(external_authority_basis: object) -> str:
    basis = render_field_value(external_authority_basis)
    if basis == "host_turn_boundary":
        return "auto_resume_any_followup"
    if basis in {"explicit_user_pause", "explicit_user_stop"}:
        return "explicit_resume_required"
    if basis == "explicit_user_redirect":
        return "redirected_by_user"
    if basis == "human_decision_required":
        return "await_human_decision"
    return "resume_command_or_followup"


def require_gate_call(run_dir: Path) -> int:
    if os.environ.get("AGENT_LOOP_CLOSEOUT_GATE") != "1":
        print("emit_pause_reply.py is internal; use closeout_gate.py", file=sys.stderr)
        return 1
    gate_run_dir = os.environ.get("AGENT_LOOP_GATE_RUN_DIR", "")
    if not gate_run_dir or Path(gate_run_dir).resolve() != run_dir:
        print("emit_pause_reply.py requires AGENT_LOOP_GATE_RUN_DIR to match the target run dir", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render and validate the low-freedom turn-ending pause reply from handoff.md.",
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
    if clean_value(str(fields.get("run_decision", ""))) != "pause":
        print("emit_pause_reply.py requires handoff.md with run_decision=pause", file=sys.stderr)
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

    resume_instructions = render_resume_instructions(fields.get("resume_instructions", ""))
    if is_noneish(resume_instructions):
        print("emit_pause_reply.py requires non-empty resume_instructions in handoff.md", file=sys.stderr)
        return 1

    reply = "\n".join(
        [
            f"loop_state={render_field_value(fields.get('loop_state', ''))}",
            f"host_resume_mode={render_field_value(fields.get('host_resume_mode', ''))}",
            f"pause_scope={render_pause_scope(fields.get('external_authority_basis', ''))}",
            f"continuation_authority={render_continuation_authority(fields.get('external_authority_basis', ''))}",
            f"semantic_state={render_semantic_state(fields.get('external_authority_basis', ''))}",
            f"followup_resume_policy={render_followup_resume_policy(fields.get('external_authority_basis', ''))}",
            f"current_or_next_stage={render_field_value(fields.get('current_or_next_stage', ''))}",
            f"next_mandatory_action={render_field_value(fields.get('next_mandatory_action', ''))}",
            f"goal_completion_status={render_field_value(fields.get('goal_completion_status', ''))}",
            f"turn_exit_cause={render_field_value(fields.get('turn_exit_cause', ''))}",
            f"turn_exit_evidence={render_field_value(fields.get('turn_exit_evidence', ''))}",
            f"pause_reason={render_field_value(fields.get('pause_reason', ''))}",
            f"external_authority_basis={render_field_value(fields.get('external_authority_basis', ''))}",
            f"resume_command={render_resume_command(run_dir)}",
            f"resume_instructions={resume_instructions}",
        ]
    ) + "\n"

    validator = Path(__file__).with_name("validate_pause_reply.py")
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
    sys.exit(main())
