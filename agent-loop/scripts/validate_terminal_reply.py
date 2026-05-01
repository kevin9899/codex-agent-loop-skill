#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from terminal_reply_summary import (
    PLANNING_COMPLETE_REPLY_PREFIXES,
    STOP_REPLY_PREFIXES,
    build_stop_reply_lines,
)
from validate_handoff import (
    CONSENT_SEEKING_PATTERNS,
    PAUSE_CLOSURE_SCENT_PATTERNS,
    REPORT_DRIVEN_PATTERNS,
    clean_value,
    contains_any_pattern,
    flatten_multivalue_text,
    is_noneish,
    parse_handoff,
)

TERMINAL_BRIEFING_OVERCLAIM_PATTERNS = [
    r"\bperfect\b",
    r"\bno risks?\b",
    r"\ball problems? solved\b",
    r"완벽",
    r"리스크\s*없음",
    r"모든\s*문제\s*해결",
]


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

    handoff_validator = Path(__file__).with_name("validate_handoff.py")
    handoff_result = subprocess.run(
        [sys.executable, str(handoff_validator), str(run_dir), "--require-consensus"],
        text=True,
        capture_output=True,
    )
    if handoff_result.returncode != 0:
        errors.append("handoff.md failed closeout validation required for a terminal reply")
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
    if run_decision not in {"stop", "planning_complete"}:
        return [f"--run-dir requires handoff run_decision=stop|planning_complete; got `{run_decision or 'missing'}`"]

    if run_decision == "stop":
        expected_lines = build_stop_reply_lines(fields, run_dir)
        if len(lines) != len(STOP_REPLY_PREFIXES):
            errors.append(f"stop reply must contain exactly {len(STOP_REPLY_PREFIXES)} non-empty lines")
        else:
            for index, prefix in enumerate(STOP_REPLY_PREFIXES):
                if not lines[index].startswith(prefix):
                    errors.append(f"line {index + 1} must start with `{prefix}`; got `{lines[index]}`")
                    continue
                reply_value = clean_value(extract_field_value(lines[index]))
                expected_value = clean_value(extract_field_value(expected_lines[index]))
                if reply_value != expected_value:
                    errors.append(f"reply field `{prefix[:-1]}` must exactly match the canonical derived stop reply")
            stop_reason_value = clean_value(extract_field_value(lines[4]))
            if contains_any_pattern(stop_reason_value, CONSENT_SEEKING_PATTERNS + REPORT_DRIVEN_PATTERNS):
                errors.append("stop reply stop_reason may not use consent-seeking or report-driven phrasing")
            if contains_any_pattern(stop_reason_value, PAUSE_CLOSURE_SCENT_PATTERNS):
                errors.append("stop reply stop_reason may not use soft-close or queued-for-later phrasing")
            for index, prefix in enumerate(STOP_REPLY_PREFIXES):
                if prefix not in {"verification_summary=", "need_to_know="}:
                    continue
                value = clean_value(extract_field_value(lines[index]))
                if contains_any_pattern(value, CONSENT_SEEKING_PATTERNS + REPORT_DRIVEN_PATTERNS):
                    errors.append(f"stop reply {prefix[:-1]} may not use consent-seeking or report-driven phrasing")
                if contains_any_pattern(value, TERMINAL_BRIEFING_OVERCLAIM_PATTERNS):
                    errors.append(f"stop reply {prefix[:-1]} may not overclaim risk-free or perfect completion")
        return errors

    if len(lines) != len(PLANNING_COMPLETE_REPLY_PREFIXES):
        errors.append(f"planning_complete reply must contain exactly {len(PLANNING_COMPLETE_REPLY_PREFIXES)} non-empty lines")
        return errors

    expected_resume = flatten_multivalue_text(fields.get("resume_instructions", ""))
    expected = {
        "loop_state=": clean_value(str(fields.get("loop_state", ""))),
        "run_decision=": run_decision,
        "current_or_next_stage=": clean_value(str(fields.get("current_or_next_stage", ""))),
        "stop_reason=": clean_value(str(fields.get("pause_reason", ""))),
        "external_authority_basis=": clean_value(str(fields.get("external_authority_basis", ""))),
        "resume_instructions=": expected_resume,
    }
    for index, prefix in enumerate(PLANNING_COMPLETE_REPLY_PREFIXES):
        if not lines[index].startswith(prefix):
            errors.append(f"line {index + 1} must start with `{prefix}`; got `{lines[index]}`")
            continue
        reply_value = clean_value(extract_field_value(lines[index]))
        if prefix == "resume_instructions=":
            if is_noneish(expected_resume):
                errors.append("planning_complete handoff requires non-empty resume_instructions")
            elif reply_value != expected_resume:
                errors.append("reply field `resume_instructions` must exactly match handoff.md")
        elif reply_value != expected[prefix]:
            errors.append(f"reply field `{prefix[:-1]}` must exactly match handoff.md")

    stop_reason_value = clean_value(extract_field_value(lines[3]))
    resume_instructions_value = clean_value(extract_field_value(lines[5]))
    if contains_any_pattern(stop_reason_value, CONSENT_SEEKING_PATTERNS + REPORT_DRIVEN_PATTERNS):
        errors.append("planning_complete stop_reason may not use consent-seeking or report-driven phrasing")
    if contains_any_pattern(resume_instructions_value, PAUSE_CLOSURE_SCENT_PATTERNS + CONSENT_SEEKING_PATTERNS + REPORT_DRIVEN_PATTERNS):
        errors.append("planning_complete resume_instructions may not use closure-scent, consent-seeking, or report-driven phrasing")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a terminal agent-loop closeout reply against handoff.md.",
    )
    parser.add_argument(
        "reply_path",
        nargs="?",
        help="Optional path to a text file. If omitted, read the reply from stdin.",
    )
    parser.add_argument(
        "--run-dir",
        required=True,
        help="Agent-loop run directory whose handoff.md should authorize this terminal reply.",
    )
    args = parser.parse_args()

    lines = non_empty_lines(load_text(args.reply_path))
    errors = validate_run_dir(args.run_dir, lines)

    if errors:
        print("[FAIL] terminal-reply validation failed")
        for error in errors:
            print(f"- {error}")
        return 1

    print("[OK] terminal-reply validation passed")
    print(f"run_dir={Path(args.run_dir).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
