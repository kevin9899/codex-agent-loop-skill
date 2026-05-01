#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

from validate_handoff import (
    clean_value,
    has_unverified_local_edit_signal,
    is_inspection_only_continue_exit,
    is_open_ended_candidate_hunt,
    parse_handoff,
)

REQUIRED_FIELDS = [
    "loop_state=",
    "run_decision=",
    "semantic_state=",
    "continuation_authority=",
    "current_or_next_stage=",
    "next_mandatory_action=",
    "goal_completion_status=",
    "turn_exit_cause=",
    "turn_exit_evidence=",
]

TAIL_FIELDS = [
    "active_delta=",
    "stop_status=",
    "forced_boundary_note=",
    "host_boundary_effect=",
    "auto_resume_trigger=",
    "followup_resume_policy=",
    "resume_command=",
    "blocking_or_risk=",
]

TAIL_ORDER = [
    "active_delta=",
    "stop_status=",
    "forced_boundary_note=",
    "host_boundary_effect=",
    "auto_resume_trigger=",
    "followup_resume_policy=",
    "resume_command=",
    "blocking_or_risk=",
]

CLOSURE_SCENT_PATTERNS = [
    r"완료",
    r"마무리",
    r"정리",
    r"\b끝\b",
    r"\bdone\b",
    r"\bcompleted\b",
    r"\bfinished\b",
    r"\bwrap(?:ped)? up\b",
    r"\bqueued\b",
    r"\bresume\b",
    r"\bnext loop\b",
    r"\bpick up\b",
    r"\bif needed\b",
    r"\bif you want\b",
    r"\bwhen you are ready\b",
    r"\bif you are ready\b",
    r"\bcan take\b",
    r"\bcould\b",
    r"\bawaiting\b",
    r"\bstatus update\b",
    r"\bprogress update\b",
    r"\bcheck-?in\b",
    r"\breport(?:ing)?\b",
    r"\bcontinue\?\b",
    r"\bresume\?\b",
    r"\bshall i\b",
    r"\bshould i\b",
    r"\bwant me to\b",
    r"\bdo you want me to\b",
    r"\btell me whether to proceed\b",
    r"다음 루프",
    r"재개",
    r"이어서",
    r"필요하면",
    r"원하면",
    r"대기",
    r"준비되면",
    r"말해주시면",
    r"상태 보고",
    r"진행 보고",
    r"중간 보고",
    r"체크인",
    r"계속할까요",
    r"진행할까요",
    r"이어갈까요",
]

CONTINUE_EXIT_ALLOWED = {
    "next_action_started",
    "blocked_during_attempt",
}

ACTIVE_DELTA_ACTION_PATTERNS = [
    r"\bspawn(?:ed|ing)?\b",
    r"\bdispatch(?:ed|ing)?\b",
    r"\bdelegat(?:e|ed|ing|ion)\b",
    r"\battempt(?:ed|ing)?\b",
    r"\bretry(?:ing)?\b",
    r"\bedit(?:ed|ing)?\b",
    r"\bpatch(?:ed|ing)?\b",
    r"\bupdate(?:d|ing)?\b",
    r"\bchange(?:d|ing)?\b",
    r"\bimplement(?:ed|ing)?\b",
    r"\bran\b",
    r"\brun(?:ning)?\b",
    r"\bexecute(?:d|ing)?\b",
    r"\blaunch(?:ed|ing)?\b",
    r"\bcapture(?:d|ing)?\b",
    r"\bwrite(?:s|ing|en)?\b",
    r"\bcreate(?:d|ing)?\b",
    r"\badd(?:ed|ing)?\b",
    r"\bremove(?:d|ing)?\b",
    r"\bfix(?:ed|ing)?\b",
    r"\btest(?:ed|ing)?\b",
    r"\bvitest\b",
    r"\beslint\b",
    r"\btypecheck\b",
    r"\bbuild\b",
    r"수정",
    r"패치",
    r"적용",
    r"실행",
    r"재실행",
    r"캡처",
    r"구현",
    r"작성",
    r"변경",
    r"추가",
    r"제거",
    r"테스트",
    r"검증",
]

COMPOUND_NEXT_ACTION_PATTERNS = [
    r"\band\b",
    r"\bor\b",
    r"\bthen\b",
    r"그리고",
    r"또는",
    r"그 다음",
]

FORCED_BOUNDARY_NOTE = (
    "호스트 때문에 보이는 답변만 한번 끊겼고 루프는 멈추지 않았습니다. "
    "아무 후속 메시지나 보내면 같은 run을 즉시 이어갑니다."
)


def load_text(path_arg: str | None) -> str:
    if path_arg:
        return Path(path_arg).read_text(encoding="utf-8").lstrip("\ufeff")
    return sys.stdin.read().lstrip("\ufeff")


def non_empty_lines(text: str) -> list[str]:
    return [line.rstrip() for line in text.splitlines() if line.strip()]


def is_noneish_text(value: str) -> bool:
    text = clean_value(value).lower()
    if not text:
        return True
    return (
        text == "none"
        or text == "n/a"
        or text == "na"
        or text.startswith("none ")
        or text.startswith("none-")
        or text.startswith("none -")
    )


def extract_field_value(line: str) -> str:
    return line.split("=", 1)[1] if "=" in line else ""


def extract_anchor_tokens(text: str) -> set[str]:
    tokens = re.findall(r"[A-Za-z0-9_-]{3,}|[가-힣]{2,}", text.lower())
    stopwords = {
        "the",
        "and",
        "for",
        "with",
        "that",
        "this",
        "from",
        "after",
        "before",
        "into",
        "while",
        "already",
        "started",
        "action",
        "stage",
        "current",
        "next",
        "active",
        "delta",
        "blocking",
        "risk",
        "using",
        "used",
        "turn",
        "reply",
        "run",
        "dir",
        "none",
    }
    return {token for token in tokens if token not in stopwords}


def contains_closure_scent(text: str) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in CLOSURE_SCENT_PATTERNS)


def contains_forbidden_tail_closure_scent(field_name: str, text: str) -> bool:
    if field_name in {
        "stop_status",
        "forced_boundary_note",
        "host_boundary_effect",
        "auto_resume_trigger",
        "followup_resume_policy",
        "resume_command",
    }:
        return False
    return contains_closure_scent(text)


def contains_active_delta_action(text: str) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in ACTIVE_DELTA_ACTION_PATTERNS)


def is_compound_next_action(text: str) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in COMPOUND_NEXT_ACTION_PATTERNS)


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
        errors.append("handoff.md failed closeout validation required for a continue reply")
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
    if run_decision != "continue":
        errors.append(f"--run-dir requires handoff run_decision=continue; got `{run_decision or 'missing'}`")

    host_resume_mode = clean_value(str(fields.get("host_resume_mode", "")))

    continue_exit_status = clean_value(str(fields.get("continue_exit_status", "")))
    if continue_exit_status not in CONTINUE_EXIT_ALLOWED:
        errors.append(
            "handoff continue_exit_status must be `next_action_started` or `blocked_during_attempt` for a turn-ending continue reply"
        )

    continue_exit_evidence = clean_value(str(fields.get("continue_exit_evidence", "")))
    if is_noneish_text(continue_exit_evidence):
        errors.append("handoff continue_exit_evidence must record what was started or what blocked the attempt")
    if is_inspection_only_continue_exit(continue_exit_status, continue_exit_evidence):
        errors.append("handoff continue_exit_evidence cannot be inspection-only when continue_exit_status=next_action_started")
    if has_unverified_local_edit_signal(continue_exit_evidence):
        errors.append(
            "handoff continue_exit_evidence may not end on local-edit-only progress without matching targeted validation proof"
        )

    handoff_next_action = clean_value(str(fields.get("next_mandatory_action", "")))
    if is_noneish_text(handoff_next_action):
        errors.append("handoff next_mandatory_action must remain live when validating a continue reply")
    elif is_compound_next_action(handoff_next_action):
        errors.append("handoff next_mandatory_action must stay atomic for a turn-ending continue reply")
    elif is_open_ended_candidate_hunt(handoff_next_action):
        errors.append(
            "handoff next_mandatory_action may not remain a pure triage/sweep/candidate-hunt state for a turn-ending continue reply"
        )

    turn_exit_cause = clean_value(str(fields.get("turn_exit_cause", "")))
    if turn_exit_cause == "not_applicable" or not turn_exit_cause:
        errors.append("handoff turn_exit_cause must explain why a turn-ending continue reply is unavoidable")
    if host_resume_mode == "same_turn_only" and turn_exit_cause != "host_turn_boundary_pause":
        errors.append("host_resume_mode=same_turn_only continue replies require turn_exit_cause=host_turn_boundary_pause")

    turn_exit_evidence = clean_value(str(fields.get("turn_exit_evidence", "")))
    if is_noneish_text(turn_exit_evidence):
        errors.append("handoff turn_exit_evidence must record the concrete boundary that forced the continue reply")

    tail_start = len(REQUIRED_FIELDS)

    if len(lines) >= tail_start:
        reply_loop_state = clean_value(extract_field_value(lines[0]))
        handoff_loop_state = clean_value(str(fields.get("loop_state", "")))
        if handoff_loop_state and reply_loop_state != handoff_loop_state:
            errors.append("reply loop_state must exactly match handoff.md when --run-dir is provided")

        reply_run_decision = clean_value(extract_field_value(lines[1]))
        if reply_run_decision != "continue":
            errors.append("reply run_decision must be continue")

        reply_semantic_state = clean_value(extract_field_value(lines[2]))
        if host_resume_mode == "same_turn_only" and reply_semantic_state != "incomplete_forced_boundary":
            errors.append("same_turn_only continue replies require semantic_state=incomplete_forced_boundary")

        reply_continuation_authority = clean_value(extract_field_value(lines[3]))
        if reply_continuation_authority != "standing":
            errors.append("continue replies require continuation_authority=standing")

        reply_stage = clean_value(extract_field_value(lines[4]))
        handoff_stage = clean_value(str(fields.get("current_or_next_stage", "")))
        if handoff_stage and reply_stage != handoff_stage:
            errors.append("reply current_or_next_stage must exactly match handoff.md when --run-dir is provided")

        reply_next_action = clean_value(lines[5][len("next_mandatory_action="):])
        if handoff_next_action and reply_next_action != handoff_next_action:
            errors.append("reply next_mandatory_action must exactly match handoff.md when --run-dir is provided")

        reply_goal_status = clean_value(extract_field_value(lines[6]))
        handoff_goal_status = clean_value(str(fields.get("goal_completion_status", "")))
        if handoff_goal_status and reply_goal_status != handoff_goal_status:
            errors.append("reply goal_completion_status must exactly match handoff.md when --run-dir is provided")

        reply_turn_exit_cause = clean_value(extract_field_value(lines[7]))
        if turn_exit_cause and reply_turn_exit_cause != turn_exit_cause:
            errors.append("reply turn_exit_cause must exactly match handoff.md when --run-dir is provided")

        reply_turn_exit_evidence = clean_value(lines[8][len("turn_exit_evidence="):])
        if turn_exit_evidence and reply_turn_exit_evidence != turn_exit_evidence:
            errors.append("reply turn_exit_evidence must exactly match handoff.md when --run-dir is provided")

    if continue_exit_status == "blocked_during_attempt":
        if not any(line.startswith("blocking_or_risk=") for line in lines[tail_start:]):
            errors.append("blocked_during_attempt requires a `blocking_or_risk=` line in the reply tail")

    tail_fields: dict[str, str] = {}
    for line in lines[tail_start:]:
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        tail_fields[key] = clean_value(value)

    stop_status = tail_fields.get("stop_status", "")
    if stop_status != "not_stopped":
        errors.append("continue replies require `stop_status=not_stopped`")

    if host_resume_mode == "same_turn_only":
        host_boundary_effect = tail_fields.get("host_boundary_effect", "")
        if host_boundary_effect != "visible_turn_only_not_goal_stop":
            errors.append(
                "host_resume_mode=same_turn_only continue replies require `host_boundary_effect=visible_turn_only_not_goal_stop`"
            )

        forced_boundary_note = tail_fields.get("forced_boundary_note", "")
        if forced_boundary_note != FORCED_BOUNDARY_NOTE:
            errors.append(
                "host_resume_mode=same_turn_only continue replies require the explicit non-stop `forced_boundary_note=` line"
            )

        auto_resume_trigger = tail_fields.get("auto_resume_trigger", "")
        if auto_resume_trigger != "any_followup_message":
            errors.append(
                "host_resume_mode=same_turn_only continue replies require `auto_resume_trigger=any_followup_message`"
            )

        policy_value = tail_fields.get("followup_resume_policy", "")
        if policy_value != "auto_resume_any_followup":
            errors.append(
                "host_resume_mode=same_turn_only continue replies require `followup_resume_policy=auto_resume_any_followup`"
            )

        resume_command = tail_fields.get("resume_command", "")
        if not resume_command:
            errors.append("host_resume_mode=same_turn_only continue replies require a `resume_command=` line")
        elif not resume_command.startswith("$loop "):
            errors.append("resume_command must start with `$loop `")
        else:
            expected_absolute = f"$loop {run_dir}"
            try:
                expected_relative = f"$loop {run_dir.relative_to(Path.cwd().resolve()).as_posix()}"
            except ValueError:
                expected_relative = expected_absolute
            if resume_command not in {expected_absolute, expected_relative}:
                errors.append("resume_command must point at the validated run directory")

    active_delta = ""
    blocking_or_risk = ""
    for line in lines[tail_start:]:
        if line.startswith("active_delta="):
            active_delta = clean_value(extract_field_value(line))
        elif line.startswith("blocking_or_risk="):
            blocking_or_risk = clean_value(extract_field_value(line))
    if active_delta:
        active_tokens = extract_anchor_tokens(active_delta)
        next_action_tokens = extract_anchor_tokens(handoff_next_action)
        continue_exit_tokens = extract_anchor_tokens(continue_exit_evidence)
        if active_tokens and next_action_tokens and not (active_tokens & next_action_tokens):
            errors.append("active_delta must stay anchored to next_mandatory_action")
        if active_tokens and continue_exit_tokens and not (active_tokens & continue_exit_tokens):
            errors.append("active_delta must stay anchored to continue_exit_evidence")
        if not contains_active_delta_action(active_delta):
            errors.append("active_delta must describe an in-flight concrete action, not a recap-only summary")
        if is_open_ended_candidate_hunt(active_delta):
            errors.append(
                "active_delta may not describe a pure triage/sweep/candidate-hunt state for a turn-ending continue reply"
            )
        if has_unverified_local_edit_signal(active_delta):
            errors.append(
                "active_delta may not describe local edits without matching targeted validation proof in a turn-ending continue reply"
            )
    if continue_exit_status == "blocked_during_attempt" and blocking_or_risk:
        blocking_tokens = extract_anchor_tokens(blocking_or_risk)
        next_action_tokens = extract_anchor_tokens(handoff_next_action)
        if blocking_tokens and next_action_tokens and not (blocking_tokens & next_action_tokens):
            errors.append("blocking_or_risk must stay anchored to the same blocked next_mandatory_action")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a nonstop $loop continue-reply against the low-freedom final contract.",
    )
    parser.add_argument(
        "reply_path",
        nargs="?",
        help="Optional path to a text file. If omitted, read the reply from stdin.",
    )
    parser.add_argument(
        "--run-dir",
        help="Optional agent-loop run directory. When provided, require matching continue-exit proof in handoff.md.",
    )
    args = parser.parse_args()

    text = load_text(args.reply_path)
    lines = non_empty_lines(text)
    errors: list[str] = []

    if not args.run_dir:
        errors.append("turn-ending continue reply validation requires --run-dir")

    tail_start = len(REQUIRED_FIELDS)

    if len(lines) < tail_start:
        errors.append(f"reply must contain at least the {tail_start} required live-state lines")
    else:
        for index, prefix in enumerate(REQUIRED_FIELDS):
            if not lines[index].startswith(prefix):
                errors.append(
                    f"line {index + 1} must start with `{prefix}`; got `{lines[index]}`"
                )
        if not errors:
            loop_state_value = clean_value(extract_field_value(lines[0]))
            run_decision_value = clean_value(extract_field_value(lines[1]))
            semantic_state_value = clean_value(extract_field_value(lines[2]))
            continuation_authority_value = clean_value(extract_field_value(lines[3]))
            current_stage_value = clean_value(extract_field_value(lines[4]))
            next_action_value = clean_value(extract_field_value(lines[5]))
            goal_status_value = clean_value(extract_field_value(lines[6]))
            turn_exit_cause_value = clean_value(extract_field_value(lines[7]))
            turn_exit_evidence_value = clean_value(extract_field_value(lines[8]))
            if is_noneish_text(loop_state_value):
                errors.append("loop_state line must carry a live value")
            if loop_state_value in {"paused", "stopped"}:
                errors.append("continue reply cannot use loop_state paused/stopped")
            if run_decision_value != "continue":
                errors.append("run_decision line must be continue")
            if semantic_state_value not in {"incomplete_forced_boundary", "in_progress_continue"}:
                errors.append("semantic_state must be incomplete_forced_boundary or in_progress_continue")
            if continuation_authority_value != "standing":
                errors.append("continuation_authority must be standing")
            if is_noneish_text(current_stage_value):
                errors.append("current_or_next_stage line must carry a live value")
            elif contains_closure_scent(current_stage_value):
                errors.append("current_or_next_stage may not use closure-scent phrasing in a continue reply")
            if is_noneish_text(next_action_value):
                errors.append("next_mandatory_action line must carry a live value")
            elif contains_closure_scent(next_action_value):
                errors.append("next_mandatory_action may not use closure-scent phrasing in a continue reply")
            elif is_compound_next_action(next_action_value):
                errors.append("next_mandatory_action must stay atomic in a continue reply")
            if is_noneish_text(goal_status_value):
                errors.append("goal_completion_status line must carry a live value")
            if turn_exit_cause_value == "not_applicable" or is_noneish_text(turn_exit_cause_value):
                errors.append("turn_exit_cause line must carry the forced boundary reason")
            if is_noneish_text(turn_exit_evidence_value):
                errors.append("turn_exit_evidence line must carry concrete boundary evidence")

    tail = lines[tail_start:]
    if not tail:
        errors.append("reply tail must include an `active_delta=` line after the live-state fields")
    else:
        if not tail[0].startswith(TAIL_FIELDS[0]):
            errors.append("reply tail must start with `active_delta=` immediately after the live-state fields")

        seen_tail_fields: list[str] = []
        previous_order_index = -1

        for line in tail:
            if not any(line.startswith(prefix) for prefix in TAIL_FIELDS):
                errors.append(f"reply tail may only use {TAIL_FIELDS}; got `{line}`")
                continue
            matching_prefix = next(prefix for prefix in TAIL_FIELDS if line.startswith(prefix))
            field_name = matching_prefix[:-1]
            order_index = TAIL_ORDER.index(matching_prefix)
            if field_name in seen_tail_fields:
                errors.append(f"reply tail contains duplicate `{field_name}=` line")
            seen_tail_fields.append(field_name)
            if order_index < previous_order_index:
                errors.append("reply tail fields must stay in canonical order")
            previous_order_index = order_index
            value = clean_value(extract_field_value(line))
            if is_noneish_text(value):
                errors.append(f"{field_name} must carry a concrete value")
                continue
            if contains_forbidden_tail_closure_scent(field_name, value):
                errors.append(f"{field_name} contains closure-scent phrasing while the run is still continuing")

    if args.run_dir:
        errors.extend(validate_run_dir(args.run_dir, lines))

    if errors:
        print("[FAIL] continue-reply validation failed")
        for error in errors:
            print(f"- {error}")
        return 1

    print("[OK] continue-reply validation passed")
    print(f"lines={len(lines)}")
    if args.run_dir:
        print(f"run_dir={Path(args.run_dir).resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
