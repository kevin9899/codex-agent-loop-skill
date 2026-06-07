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
    "user_visible_note=",
    "final_copy_policy=",
    "forced_boundary_note=",
    "host_boundary_effect=",
    "auto_resume_trigger=",
    "followup_resume_policy=",
    "resume_command=",
    "blocking_or_risk=",
    "user_visible_status_ko=",
    "blocked_action_ko=",
    "needed_condition_ko=",
    "human_readable_reason=",
]

TAIL_ORDER = [
    "active_delta=",
    "user_visible_status_ko=",
    "blocked_action_ko=",
    "needed_condition_ko=",
    "human_readable_reason=",
    "stop_status=",
    "user_visible_note=",
    "final_copy_policy=",
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
VAGUE_BLOCKER_KO_PATTERNS = [
    r"확인\s*필요",
    r"대기",
    r"나중에",
    r"추후",
    r"언젠가",
]
EXTERNAL_GATE_ONLY_PATTERNS = [
    r"\bno bounded local actions? remain\b",
    r"\bno local actions? remain\b",
    r"\bexternal[- ]only\b",
    r"\bexternal gate\b",
    r"\bhuman decision\b",
    r"\bexplicit mutation authority\b",
    r"\bbranch[- ]protection mutation authority\b",
    r"\bstable green\b",
    r"\brequired_status_checks\b",
    r"\bruleset\b",
    r"외부 조건",
    r"외부 게이트",
    r"로컬 작업.*없",
    r"명시적인.*권한",
]

USER_HANDBACK_PATTERNS = [
    r"\buser must\b",
    r"\buser needs to\b",
    r"\buser has to\b",
    r"\bhave the user\b",
    r"\bask the user\b",
    r"\bwait for the user\b",
    r"사용자가\s*.*(해야|종료|승인|제공|처리)",
    r"사용자\s*(종료|승인|제공|처리|대기)",
    r"유저가\s*.*(해야|종료|승인|제공|처리)",
]


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
        "user_visible_note",
        "forced_boundary_note",
        "user_visible_status_ko",
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


def contains_korean(text: str) -> bool:
    return bool(re.search(r"[가-힣]", text))


def contains_vague_blocker_ko(text: str) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in VAGUE_BLOCKER_KO_PATTERNS)


def contains_user_handback(text: str) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in USER_HANDBACK_PATTERNS)


def is_external_gate_only_continue(*values: str) -> bool:
    combined = " ".join(clean_value(value).lower() for value in values if clean_value(value))
    if not combined:
        return False
    return any(re.search(pattern, combined, flags=re.IGNORECASE) for pattern in EXTERNAL_GATE_ONLY_PATTERNS)


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
        if (
            host_resume_mode != "same_turn_only"
            and continue_exit_status == "blocked_during_attempt"
            and reply_semantic_state not in {"incomplete_blocked_pending_external", "incomplete_blocked_pending_human"}
        ):
            errors.append("durable blocked continue replies require semantic_state=incomplete_blocked_pending_*")

        reply_continuation_authority = clean_value(extract_field_value(lines[3]))
        if host_resume_mode == "same_turn_only" and reply_continuation_authority != "standing":
            errors.append("same_turn_only continue replies require continuation_authority=standing")
        if (
            host_resume_mode != "same_turn_only"
            and continue_exit_status == "blocked_during_attempt"
            and reply_continuation_authority not in {"blocked_pending_external", "blocked_pending_human"}
        ):
            errors.append("durable blocked continue replies require continuation_authority=blocked_pending_*")

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
        if not any(line.startswith("user_visible_status_ko=") for line in lines[tail_start:]):
            errors.append("blocked_during_attempt requires a `user_visible_status_ko=` line before stop_status")
        if not any(line.startswith("blocked_action_ko=") for line in lines[tail_start:]):
            errors.append("blocked_during_attempt requires a `blocked_action_ko=` line before stop_status")
        if not any(line.startswith("needed_condition_ko=") for line in lines[tail_start:]):
            errors.append("blocked_during_attempt requires a `needed_condition_ko=` line before stop_status")
        if not any(line.startswith("human_readable_reason=") for line in lines[tail_start:]):
            errors.append("blocked_during_attempt requires a `human_readable_reason=` line before stop_status")
        if is_external_gate_only_continue(
            handoff_next_action,
            continue_exit_evidence,
            turn_exit_evidence,
            clean_value(str(fields.get("blocking_findings", ""))),
        ):
            errors.append(
                "external-gate-only blocked states may not emit auto-resume continue receipts; run completion proof and stop when source criteria allow, or encode a truthful external-gate pause"
            )

    tail_fields: dict[str, str] = {}
    for line in lines[tail_start:]:
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        tail_fields[key] = clean_value(value)

    stop_status = tail_fields.get("stop_status", "")
    if stop_status != "not_stopped":
        errors.append("continue replies require `stop_status=not_stopped`")

    if continue_exit_status == "blocked_during_attempt":
        user_visible_status_ko = tail_fields.get("user_visible_status_ko", "")
        if user_visible_status_ko != USER_VISIBLE_STATUS_KO:
            errors.append("blocked_during_attempt replies require the exact explicit `user_visible_status_ko=` non-completion note")

        blocked_action_ko = tail_fields.get("blocked_action_ko", "")
        needed_condition_ko = tail_fields.get("needed_condition_ko", "")
        human_readable_reason = tail_fields.get("human_readable_reason", "")
        for field_name, value in {
            "blocked_action_ko": blocked_action_ko,
            "needed_condition_ko": needed_condition_ko,
            "human_readable_reason": human_readable_reason,
        }.items():
            if is_noneish_text(value):
                errors.append(f"blocked_during_attempt replies require a concrete `{field_name}=` value")
            elif not contains_korean(value):
                errors.append(f"`{field_name}=` must be Korean user-facing text")
            elif contains_vague_blocker_ko(value):
                errors.append(f"`{field_name}=` must name the concrete blocked action or condition, not vague timing text")
            elif field_name in {"needed_condition_ko", "human_readable_reason"} and contains_user_handback(value):
                errors.append(
                    f"`{field_name}=` must describe a controller-owned retry/probe or a recorded no-bounded-action proof, not hand work back to the user"
                )

    user_visible_note = tail_fields.get("user_visible_note", "")
    if user_visible_note != USER_VISIBLE_CONTINUE_NOTE:
        errors.append(
            "continue replies require the explicit user-facing `user_visible_note=` line"
        )

    final_copy_policy = tail_fields.get("final_copy_policy", "")
    if final_copy_policy != FINAL_COPY_POLICY:
        errors.append(
            "continue replies require `final_copy_policy=copy_closeout_gate_stdout_verbatim_no_summary_no_omission`"
        )

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
            if semantic_state_value not in {
                "incomplete_forced_boundary",
                "in_progress_continue",
                "incomplete_blocked_pending_external",
                "incomplete_blocked_pending_human",
            }:
                errors.append("semantic_state must be a valid incomplete continue state")
            if continuation_authority_value not in {
                "standing",
                "blocked_pending_external",
                "blocked_pending_human",
            }:
                errors.append("continuation_authority must be standing or blocked_pending_*")
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
