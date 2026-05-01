#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from validate_handoff import (
    CONSENT_SEEKING_PATTERNS,
    PAUSE_CLOSURE_SCENT_PATTERNS,
    REPORT_DRIVEN_PATTERNS,
    clean_value,
    contains_any_pattern,
    is_noneish,
    parse_handoff,
)

REQUIRED_FIELDS = [
    "loop_state=",
    "current_or_next_stage=",
    "next_mandatory_action=",
]

OPTIONAL_FIELD = "blocking_or_risk="


def load_text(path_arg: str | None) -> str:
    if path_arg:
        return Path(path_arg).read_text(encoding="utf-8").lstrip("\ufeff")
    return sys.stdin.read().lstrip("\ufeff")


def non_empty_lines(text: str) -> list[str]:
    return [line.rstrip() for line in text.splitlines() if line.strip()]


def extract_field_value(line: str) -> str:
    return line.split("=", 1)[1] if "=" in line else ""


def validate_run_dir(run_dir_arg: str, lines: list[str]) -> list[str]:
    run_dir = Path(run_dir_arg).resolve()
    handoff_path = run_dir / "handoff.md"
    errors: list[str] = []

    if not handoff_path.exists():
        return [f"handoff.md not found under run dir: {run_dir}"]

    fields = parse_handoff(handoff_path)
    run_decision = clean_value(str(fields.get("run_decision", "")))
    loop_state = clean_value(str(fields.get("loop_state", "")))
    host_resume_mode = clean_value(str(fields.get("host_resume_mode", "")))
    if run_decision != "continue":
        errors.append(f"status reply requires an active run_decision=continue handoff; got `{run_decision or 'missing'}`")
    if loop_state in {"paused", "stopped"}:
        errors.append("status reply requires a live non-paused handoff loop_state")
    if host_resume_mode == "same_turn_only":
        errors.append("status reply is illegal when host_resume_mode=same_turn_only; persist a truthful pause instead")

    if len(lines) >= 3:
        expected = {
            "loop_state=": loop_state,
            "current_or_next_stage=": clean_value(str(fields.get("current_or_next_stage", ""))),
            "next_mandatory_action=": clean_value(str(fields.get("next_mandatory_action", ""))),
        }
        for index, prefix in enumerate(REQUIRED_FIELDS):
            reply_value = clean_value(extract_field_value(lines[index]))
            if reply_value != expected[prefix]:
                errors.append(f"reply field `{prefix[:-1]}` must exactly match handoff.md when --run-dir is provided")

        if len(lines) == 4:
            reply_blocking = clean_value(extract_field_value(lines[3]))
            if is_noneish(reply_blocking):
                errors.append("blocking_or_risk must be concrete when present")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a live-state agent-loop status reply.",
    )
    parser.add_argument(
        "reply_path",
        nargs="?",
        help="Optional path to a text file. If omitted, read the reply from stdin.",
    )
    parser.add_argument(
        "--run-dir",
        required=True,
        help="Agent-loop run directory whose handoff.md should authorize this status reply.",
    )
    args = parser.parse_args()

    lines = non_empty_lines(load_text(args.reply_path))
    errors: list[str] = []

    if len(lines) < 3 or len(lines) > 4:
        errors.append("status reply must contain 3 required lines and optional blocking_or_risk only")
    else:
        for index, prefix in enumerate(REQUIRED_FIELDS):
            if not lines[index].startswith(prefix):
                errors.append(f"line {index + 1} must start with `{prefix}`; got `{lines[index]}`")

        if len(lines) == 4 and not lines[3].startswith(OPTIONAL_FIELD):
            errors.append(f"line 4 may only use `{OPTIONAL_FIELD}`")

        if not errors:
            for line in lines:
                value = clean_value(extract_field_value(line))
                field_name = line.split("=", 1)[0]
                if is_noneish(value):
                    errors.append(f"{field_name} must carry a concrete live value")
                    continue
                if contains_any_pattern(value, PAUSE_CLOSURE_SCENT_PATTERNS + CONSENT_SEEKING_PATTERNS + REPORT_DRIVEN_PATTERNS):
                    errors.append(f"{field_name} may not use closure-scent, consent-seeking, or report-driven phrasing in a status reply")

    errors.extend(validate_run_dir(args.run_dir, lines))

    if errors:
        print("[FAIL] status-reply validation failed")
        for error in errors:
            print(f"- {error}")
        return 1

    print("[OK] status-reply validation passed")
    print(f"run_dir={Path(args.run_dir).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
