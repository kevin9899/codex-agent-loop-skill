#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from validate_handoff import clean_value, parse_handoff

FORCED_BOUNDARY_NOTE = (
    "호스트가 백그라운드 실행을 이어주지 않아 final 채널로 경계 영수증을 남긴 것입니다. "
    "루프는 목표 완료/정지로 처리되지 않았고, 아무 후속 메시지나 보내면 같은 run을 즉시 이어갑니다."
)
USER_VISIBLE_CONTINUE_NOTE = (
    "사용자 표시용: 멈춘 게 아니라 호스트가 보이는 답변만 한 번 끊은 상태입니다. "
    "다음 메시지는 같은 run 자동 재개 신호입니다."
)
FINAL_COPY_POLICY = "copy_closeout_gate_stdout_verbatim_no_summary_no_omission"
USER_VISIBLE_STATUS_KO = (
    "멈춘 것이 아닙니다. final 채널에 남긴 강제 턴 경계 영수증이며, "
    "아무 후속 메시지나 보내면 같은 run을 자동 재개합니다."
)


def require_gate_call(run_dir: Path) -> int:
    if os.environ.get("AGENT_LOOP_CLOSEOUT_GATE") != "1":
        print("emit_continue_reply.py is internal; use closeout_gate.py", file=sys.stderr)
        return 1
    gate_run_dir = os.environ.get("AGENT_LOOP_GATE_RUN_DIR", "")
    if not gate_run_dir or Path(gate_run_dir).resolve() != run_dir:
        print("emit_continue_reply.py requires AGENT_LOOP_GATE_RUN_DIR to match the target run dir", file=sys.stderr)
        return 1
    return 0


def display_run_dir(run_dir: Path) -> str:
    try:
        return run_dir.relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return str(run_dir)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render and validate the low-freedom turn-ending continue reply from handoff.md.",
    )
    parser.add_argument("run_dir", help="Path to the agent-loop run directory")
    parser.add_argument("--active-delta", required=True, help="Concrete in-flight delta for the started next action")
    parser.add_argument("--blocking-or-risk", help="Optional blocker or risk line")
    parser.add_argument("--blocked-action-ko", help="Korean description of the blocked action for blocked_during_attempt")
    parser.add_argument("--needed-condition-ko", help="Korean description of the required external/user condition for blocked_during_attempt")
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
    if clean_value(str(fields.get("run_decision", ""))) != "continue":
        print("emit_continue_reply.py requires handoff.md with run_decision=continue", file=sys.stderr)
        return 1
    host_resume_mode = clean_value(str(fields.get("host_resume_mode", "")))
    continue_exit_status = clean_value(str(fields.get("continue_exit_status", "")))
    if continue_exit_status == "blocked_during_attempt":
        if not clean_value(args.blocked_action_ko or ""):
            print("emit_continue_reply.py requires --blocked-action-ko for blocked_during_attempt", file=sys.stderr)
            return 1
        if not clean_value(args.needed_condition_ko or ""):
            print("emit_continue_reply.py requires --needed-condition-ko for blocked_during_attempt", file=sys.stderr)
            return 1
    if host_resume_mode == "same_turn_only":
        semantic_state = "incomplete_forced_boundary"
        continuation_authority = "standing"
    elif continue_exit_status == "blocked_during_attempt":
        semantic_state = "incomplete_blocked_pending_external"
        continuation_authority = "blocked_pending_external"
    else:
        semantic_state = "in_progress_continue"
        continuation_authority = "standing"
    lines = [
        f"loop_state={clean_value(str(fields.get('loop_state', '')))}",
        f"run_decision={clean_value(str(fields.get('run_decision', '')))}",
        f"semantic_state={semantic_state}",
        f"continuation_authority={continuation_authority}",
        f"current_or_next_stage={clean_value(str(fields.get('current_or_next_stage', '')))}",
        f"next_mandatory_action={clean_value(str(fields.get('next_mandatory_action', '')))}",
        f"goal_completion_status={clean_value(str(fields.get('goal_completion_status', '')))}",
        f"turn_exit_cause={clean_value(str(fields.get('turn_exit_cause', '')))}",
        f"turn_exit_evidence={clean_value(str(fields.get('turn_exit_evidence', '')))}",
        f"active_delta={args.active_delta.strip()}",
    ]
    if continue_exit_status == "blocked_during_attempt":
        lines.extend(
            [
                f"user_visible_status_ko={USER_VISIBLE_STATUS_KO}",
                f"blocked_action_ko={clean_value(args.blocked_action_ko or '')}",
                f"needed_condition_ko={clean_value(args.needed_condition_ko or '')}",
                f"human_readable_reason={clean_value(args.needed_condition_ko or '')}",
            ]
        )
    lines.extend(
        [
        "stop_status=not_stopped",
        f"user_visible_note={USER_VISIBLE_CONTINUE_NOTE}",
        f"final_copy_policy={FINAL_COPY_POLICY}",
        ]
    )
    if host_resume_mode == "same_turn_only":
        lines.extend(
            [
                f"forced_boundary_note={FORCED_BOUNDARY_NOTE}",
                "host_boundary_effect=visible_turn_only_not_goal_stop",
                "auto_resume_trigger=any_followup_message",
                "followup_resume_policy=auto_resume_any_followup",
                f"resume_command=$loop {display_run_dir(run_dir)}",
            ]
        )
    if args.blocking_or_risk:
        lines.append(f"blocking_or_risk={args.blocking_or_risk.strip()}")
    reply = "\n".join(lines) + "\n"

    validator = Path(__file__).with_name("validate_continue_reply.py")
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
