#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from validate_handoff import (
    CONSENT_SEEKING_PATTERNS,
    HOST_BOUNDARY_FORCE_PATTERNS,
    HOST_BOUNDARY_REASON_PATTERNS,
    PAUSE_CLOSURE_SCENT_PATTERNS,
    REPORT_DRIVEN_PATTERNS,
    VERIFIED_COMPLETE_STATUS,
    clean_value,
    contains_any_pattern,
    flatten_multivalue_text,
    has_actionable_resume_instructions,
    is_noneish,
    parse_handoff,
)

REQUIRED_FIELDS = [
    "loop_state=",
    "host_resume_mode=",
    "pause_scope=",
    "continuation_authority=",
    "semantic_state=",
    "followup_resume_policy=",
    "current_or_next_stage=",
    "next_mandatory_action=",
    "goal_completion_status=",
    "turn_exit_cause=",
    "turn_exit_evidence=",
    "pause_reason=",
    "external_authority_basis=",
    "resume_command=",
    "resume_instructions=",
]


def load_text(path_arg: str | None) -> str:
    if path_arg:
        return Path(path_arg).read_text(encoding="utf-8").lstrip("\ufeff")
    return sys.stdin.read().lstrip("\ufeff")


def non_empty_lines(text: str) -> list[str]:
    return [line.rstrip() for line in text.splitlines() if line.strip()]


def extract_field_value(line: str) -> str:
    return line.split("=", 1)[1] if "=" in line else ""


def render_field_value(value: object) -> str:
    return clean_value(str(value)).replace("`", "")


def render_resume_instructions(value: object) -> str:
    return flatten_multivalue_text(value).replace("`", "")


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


def validate_run_dir(run_dir_arg: str, lines: list[str]) -> list[str]:
    run_dir = Path(run_dir_arg).resolve()
    handoff_path = run_dir / "handoff.md"
    errors: list[str] = []

    if not handoff_path.exists():
        return [f"handoff.md not found under run dir: {run_dir}"]

    handoff_validator = Path(__file__).with_name("validate_handoff.py")
    handoff_result = subprocess.run(
        [sys.executable, str(handoff_validator), str(run_dir), "--require-consensus"],
        text=True,
        capture_output=True,
    )
    if handoff_result.returncode != 0:
        errors.append("handoff.md failed closeout validation required for a pause reply")
        for stream in (handoff_result.stdout, handoff_result.stderr):
            if not stream:
                continue
            for raw_line in stream.splitlines():
                line = raw_line.strip()
                if not line or line.startswith("[FAIL]"):
                    continue
                errors.append(f"handoff validator: {line}")
        return errors

    fields = parse_handoff(handoff_path)
    run_decision = clean_value(str(fields.get("run_decision", "")))
    if run_decision != "pause":
        errors.append(f"--run-dir requires handoff run_decision=pause; got `{run_decision or 'missing'}`")

    handoff_loop_state = render_field_value(fields.get("loop_state", ""))
    if handoff_loop_state != "paused":
        errors.append("handoff loop_state must be `paused` for a pause reply")

    handoff_host_resume_mode = render_field_value(fields.get("host_resume_mode", ""))
    if not handoff_host_resume_mode:
        errors.append("handoff host_resume_mode must stay explicit for a pause reply")

    handoff_stage = render_field_value(fields.get("current_or_next_stage", ""))
    if is_noneish(handoff_stage):
        errors.append("handoff current_or_next_stage must stay live for a pause reply")

    handoff_next_action = render_field_value(fields.get("next_mandatory_action", ""))
    if is_noneish(handoff_next_action):
        errors.append("handoff next_mandatory_action must stay live for a pause reply")

    handoff_goal_completion = render_field_value(fields.get("goal_completion_status", ""))
    if is_noneish(handoff_goal_completion):
        errors.append("handoff goal_completion_status must be concrete for a pause reply")
    elif handoff_goal_completion == VERIFIED_COMPLETE_STATUS:
        errors.append(f"pause replies may not claim goal_completion_status={VERIFIED_COMPLETE_STATUS}")

    handoff_turn_exit_cause = render_field_value(fields.get("turn_exit_cause", ""))
    if not handoff_turn_exit_cause:
        errors.append("handoff turn_exit_cause must stay explicit for a pause reply")
    handoff_turn_exit_evidence = render_field_value(fields.get("turn_exit_evidence", ""))
    if is_noneish(handoff_turn_exit_evidence):
        errors.append("handoff turn_exit_evidence must be concrete for a pause reply")

    handoff_pause_reason = render_field_value(fields.get("pause_reason", ""))
    if is_noneish(handoff_pause_reason):
        errors.append("handoff pause_reason must be concrete for a pause reply")

    handoff_external_basis = render_field_value(fields.get("external_authority_basis", ""))
    if not handoff_external_basis:
        errors.append("handoff external_authority_basis must be concrete for a pause reply")

    stop_authorization_status = clean_value(str(fields.get("stop_authorization_status", "")))
    if stop_authorization_status not in {"allow", "external_authority"}:
        errors.append("handoff stop_authorization_status must be `allow` or `external_authority` for a pause reply")

    stop_consensus_status = clean_value(str(fields.get("stop_consensus_status", "")))
    if stop_authorization_status == "allow" and stop_consensus_status != "allow_unanimous":
        errors.append("pause replies with autonomous halt authority require stop_consensus_status=allow_unanimous")
    if stop_authorization_status == "external_authority" and stop_consensus_status != "waived_external_authority":
        errors.append("pause replies with external authority require stop_consensus_status=waived_external_authority")

    stop_authorization_evidence = clean_value(str(fields.get("stop_authorization_evidence", "")))
    if is_noneish(stop_authorization_evidence):
        errors.append("handoff stop_authorization_evidence must be concrete for a pause reply")

    resume_raw = fields.get("resume_instructions", "")
    resume_instructions = render_resume_instructions(resume_raw)
    if is_noneish(resume_instructions):
        errors.append("handoff resume_instructions must be concrete for a pause reply")
    elif not has_actionable_resume_instructions(resume_raw):
        errors.append("handoff resume_instructions must contain actionable restart guidance for a pause reply")
    resume_command = render_resume_command(run_dir)
    expected_pause_scope = render_pause_scope(fields.get("external_authority_basis", ""))
    expected_continuation_authority = render_continuation_authority(fields.get("external_authority_basis", ""))
    expected_semantic_state = render_semantic_state(fields.get("external_authority_basis", ""))
    expected_followup_resume_policy = render_followup_resume_policy(fields.get("external_authority_basis", ""))

    host_resume_mode = clean_value(str(fields.get("host_resume_mode", "")))
    if handoff_external_basis == "host_turn_boundary" and host_resume_mode != "same_turn_only":
        errors.append("external_authority_basis=host_turn_boundary requires host_resume_mode=same_turn_only")
    if handoff_external_basis == "host_turn_boundary" and "host_boundary_ref=" not in stop_authorization_evidence:
        errors.append("host_turn_boundary pause replies require stop_authorization_evidence to record host_boundary_ref=<...>")
    if handoff_external_basis == "host_turn_boundary":
        if handoff_turn_exit_cause != "host_turn_boundary_pause":
            errors.append("host_turn_boundary pause replies require turn_exit_cause=host_turn_boundary_pause")
        if not contains_any_pattern(handoff_pause_reason, HOST_BOUNDARY_REASON_PATTERNS) or not contains_any_pattern(
            handoff_pause_reason, HOST_BOUNDARY_FORCE_PATTERNS
        ):
            errors.append("host_turn_boundary pause replies must describe a forced visible turn boundary")

    if len(lines) == len(REQUIRED_FIELDS):
        if render_field_value(extract_field_value(lines[0])) != handoff_loop_state:
            errors.append("reply loop_state must exactly match handoff.md when --run-dir is provided")
        if render_field_value(extract_field_value(lines[1])) != handoff_host_resume_mode:
            errors.append("reply host_resume_mode must exactly match handoff.md when --run-dir is provided")
        if render_field_value(extract_field_value(lines[2])) != expected_pause_scope:
            errors.append("reply pause_scope must exactly match the derived pause scope for handoff.md when --run-dir is provided")
        if render_field_value(extract_field_value(lines[3])) != expected_continuation_authority:
            errors.append(
                "reply continuation_authority must exactly match the derived continuation authority for handoff.md when --run-dir is provided"
            )
        if render_field_value(extract_field_value(lines[4])) != expected_semantic_state:
            errors.append("reply semantic_state must exactly match the derived semantic state for handoff.md when --run-dir is provided")
        if render_field_value(extract_field_value(lines[5])) != expected_followup_resume_policy:
            errors.append(
                "reply followup_resume_policy must exactly match the derived followup resume policy for handoff.md when --run-dir is provided"
            )
        if render_field_value(extract_field_value(lines[6])) != handoff_stage:
            errors.append("reply current_or_next_stage must exactly match handoff.md when --run-dir is provided")
        if render_field_value(extract_field_value(lines[7])) != handoff_next_action:
            errors.append("reply next_mandatory_action must exactly match handoff.md when --run-dir is provided")
        if render_field_value(extract_field_value(lines[8])) != handoff_goal_completion:
            errors.append("reply goal_completion_status must exactly match handoff.md when --run-dir is provided")
        if render_field_value(extract_field_value(lines[9])) != handoff_turn_exit_cause:
            errors.append("reply turn_exit_cause must exactly match handoff.md when --run-dir is provided")
        if render_field_value(extract_field_value(lines[10])) != handoff_turn_exit_evidence:
            errors.append("reply turn_exit_evidence must exactly match handoff.md when --run-dir is provided")
        if render_field_value(extract_field_value(lines[11])) != handoff_pause_reason:
            errors.append("reply pause_reason must exactly match handoff.md when --run-dir is provided")
        if render_field_value(extract_field_value(lines[12])) != handoff_external_basis:
            errors.append("reply external_authority_basis must exactly match handoff.md when --run-dir is provided")
        if render_field_value(extract_field_value(lines[13])) != resume_command:
            errors.append("reply resume_command must exactly match the canonical $loop run-dir resume command")
        if render_field_value(extract_field_value(lines[14])) != resume_instructions:
            errors.append("reply resume_instructions must exactly match handoff.md when --run-dir is provided")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a same-turn pause-reply against the low-freedom final contract.",
    )
    parser.add_argument(
        "reply_path",
        nargs="?",
        help="Optional path to a text file. If omitted, read the reply from stdin.",
    )
    parser.add_argument(
        "--run-dir",
        help="Optional agent-loop run directory. When provided, require exact handoff alignment.",
    )
    args = parser.parse_args()

    text = load_text(args.reply_path)
    lines = non_empty_lines(text)
    errors: list[str] = []

    if not args.run_dir:
        errors.append("pause reply validation requires --run-dir")

    if len(lines) != len(REQUIRED_FIELDS):
        errors.append(f"pause reply must contain exactly {len(REQUIRED_FIELDS)} non-empty lines")
    else:
        for index, prefix in enumerate(REQUIRED_FIELDS):
            if not lines[index].startswith(prefix):
                errors.append(f"line {index + 1} must start with `{prefix}`; got `{lines[index]}`")
        if not errors:
            loop_state_value = render_field_value(extract_field_value(lines[0]))
            host_resume_mode_value = render_field_value(extract_field_value(lines[1]))
            pause_scope_value = render_field_value(extract_field_value(lines[2]))
            continuation_authority_value = render_field_value(extract_field_value(lines[3]))
            semantic_state_value = render_field_value(extract_field_value(lines[4]))
            followup_resume_policy_value = render_field_value(extract_field_value(lines[5]))
            current_stage_value = render_field_value(extract_field_value(lines[6]))
            next_action_value = render_field_value(extract_field_value(lines[7]))
            goal_completion_value = render_field_value(extract_field_value(lines[8]))
            turn_exit_cause_value = render_field_value(extract_field_value(lines[9]))
            turn_exit_evidence_value = render_field_value(extract_field_value(lines[10]))
            pause_reason_value = render_field_value(extract_field_value(lines[11]))
            external_basis_value = render_field_value(extract_field_value(lines[12]))
            resume_command_value = render_field_value(extract_field_value(lines[13]))
            resume_value = render_field_value(extract_field_value(lines[14]))

            if loop_state_value != "paused":
                errors.append("pause reply must use loop_state=paused")
            if not host_resume_mode_value:
                errors.append("host_resume_mode line must carry a concrete value")
            if pause_scope_value not in {"host_boundary_only", "explicit_pause", "redirected", "human_decision_gate", "general_pause"}:
                errors.append("pause_scope line must carry a recognized pause scope")
            if continuation_authority_value not in {"standing", "withheld_by_user", "blocked_pending_human"}:
                errors.append("continuation_authority line must carry a recognized continuation authority state")
            if semantic_state_value not in {
                "incomplete_forced_boundary",
                "incomplete_paused_by_authority",
                "incomplete_blocked_pending_human",
                "incomplete_paused",
            }:
                errors.append("semantic_state line must carry a recognized incomplete-state marker")
            if followup_resume_policy_value not in {
                "auto_resume_any_followup",
                "explicit_resume_required",
                "redirected_by_user",
                "await_human_decision",
                "resume_command_or_followup",
            }:
                errors.append("followup_resume_policy line must carry a recognized followup-resume policy")
            if is_noneish(current_stage_value):
                errors.append("current_or_next_stage line must carry a live value")
            elif contains_any_pattern(current_stage_value, PAUSE_CLOSURE_SCENT_PATTERNS + CONSENT_SEEKING_PATTERNS):
                errors.append("current_or_next_stage may not use closure-scent or consent-seeking phrasing in a pause reply")
            if is_noneish(next_action_value):
                errors.append("next_mandatory_action line must carry a live value")
            elif contains_any_pattern(next_action_value, PAUSE_CLOSURE_SCENT_PATTERNS + CONSENT_SEEKING_PATTERNS):
                errors.append("next_mandatory_action may not use closure-scent or consent-seeking phrasing in a pause reply")
            if is_noneish(goal_completion_value):
                errors.append("goal_completion_status line must carry a concrete value")
            elif goal_completion_value == VERIFIED_COMPLETE_STATUS:
                errors.append(f"pause reply may not claim goal_completion_status={VERIFIED_COMPLETE_STATUS}")
            if not turn_exit_cause_value:
                errors.append("turn_exit_cause line must carry a concrete value")
            if is_noneish(turn_exit_evidence_value):
                errors.append("turn_exit_evidence line must carry a concrete value")
            if is_noneish(pause_reason_value):
                errors.append("pause_reason line must carry a concrete value")
            elif contains_any_pattern(pause_reason_value, PAUSE_CLOSURE_SCENT_PATTERNS + CONSENT_SEEKING_PATTERNS + REPORT_DRIVEN_PATTERNS):
                errors.append("pause_reason may not use closure-scent, consent-seeking, or report-driven phrasing in a pause reply")
            if not external_basis_value:
                errors.append("external_authority_basis line must carry a concrete value")
            if external_basis_value == "host_turn_boundary":
                if pause_scope_value != "host_boundary_only":
                    errors.append("host_turn_boundary pause reply must use pause_scope=host_boundary_only")
                if continuation_authority_value != "standing":
                    errors.append("host_turn_boundary pause reply must use continuation_authority=standing")
                if semantic_state_value != "incomplete_forced_boundary":
                    errors.append("host_turn_boundary pause reply must use semantic_state=incomplete_forced_boundary")
                if followup_resume_policy_value != "auto_resume_any_followup":
                    errors.append("host_turn_boundary pause reply must use followup_resume_policy=auto_resume_any_followup")
                if turn_exit_cause_value != "host_turn_boundary_pause":
                    errors.append("host_turn_boundary pause reply must use turn_exit_cause=host_turn_boundary_pause")
                if not contains_any_pattern(pause_reason_value, HOST_BOUNDARY_REASON_PATTERNS) or not contains_any_pattern(
                    pause_reason_value, HOST_BOUNDARY_FORCE_PATTERNS
                ):
                    errors.append("host_turn_boundary pause reply must make the forced host ceiling explicit in pause_reason")
                if not contains_any_pattern(turn_exit_evidence_value, HOST_BOUNDARY_REASON_PATTERNS) or not contains_any_pattern(
                    turn_exit_evidence_value, HOST_BOUNDARY_FORCE_PATTERNS
                ):
                    errors.append("host_turn_boundary pause reply must make the forced host ceiling explicit in turn_exit_evidence")
            if external_basis_value == "explicit_user_pause":
                if pause_scope_value != "explicit_pause":
                    errors.append("explicit_user_pause pause reply must use pause_scope=explicit_pause")
                if continuation_authority_value != "withheld_by_user":
                    errors.append("explicit_user_pause pause reply must use continuation_authority=withheld_by_user")
                if semantic_state_value != "incomplete_paused_by_authority":
                    errors.append("explicit_user_pause pause reply must use semantic_state=incomplete_paused_by_authority")
                if followup_resume_policy_value != "explicit_resume_required":
                    errors.append("explicit_user_pause pause reply must use followup_resume_policy=explicit_resume_required")
            if external_basis_value == "explicit_user_redirect":
                if pause_scope_value != "redirected":
                    errors.append("explicit_user_redirect pause reply must use pause_scope=redirected")
                if continuation_authority_value != "withheld_by_user":
                    errors.append("explicit_user_redirect pause reply must use continuation_authority=withheld_by_user")
                if semantic_state_value != "incomplete_paused_by_authority":
                    errors.append("explicit_user_redirect pause reply must use semantic_state=incomplete_paused_by_authority")
                if followup_resume_policy_value != "redirected_by_user":
                    errors.append("explicit_user_redirect pause reply must use followup_resume_policy=redirected_by_user")
            if external_basis_value == "human_decision_required":
                if pause_scope_value != "human_decision_gate":
                    errors.append("human_decision_required pause reply must use pause_scope=human_decision_gate")
                if continuation_authority_value != "blocked_pending_human":
                    errors.append("human_decision_required pause reply must use continuation_authority=blocked_pending_human")
                if semantic_state_value != "incomplete_blocked_pending_human":
                    errors.append("human_decision_required pause reply must use semantic_state=incomplete_blocked_pending_human")
                if followup_resume_policy_value != "await_human_decision":
                    errors.append("human_decision_required pause reply must use followup_resume_policy=await_human_decision")
            if not resume_command_value.startswith("$loop "):
                errors.append("resume_command line must start with `$loop ` and point at the paused run directory")
            if is_noneish(resume_value):
                errors.append("resume_instructions line must carry a concrete value")
            elif contains_any_pattern(resume_value, PAUSE_CLOSURE_SCENT_PATTERNS + CONSENT_SEEKING_PATTERNS + REPORT_DRIVEN_PATTERNS):
                errors.append("resume_instructions may not use closure-scent, consent-seeking, or report-driven phrasing in a pause reply")

    if args.run_dir:
        errors.extend(validate_run_dir(args.run_dir, lines))

    if errors:
        print("[FAIL] pause-reply validation failed")
        for error in errors:
            print(f"- {error}")
        return 1

    print("[OK] pause-reply validation passed")
    print(f"lines={len(lines)}")
    if args.run_dir:
        print(f"run_dir={Path(args.run_dir).resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
